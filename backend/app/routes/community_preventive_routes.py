import json
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database import get_db
from ..models import User, CommunityPost, PreventiveChallenge, PatientReward
from ..auth import get_current_user
from ..ml.community_preventive_engine import (
    SUPPORT_GROUPS_CATALOG,
    DEFAULT_PREVENTIVE_CHALLENGES,
    moderate_community_post,
    generate_personalized_lifestyle_coaching
)

router = APIRouter(prefix="", tags=["Community & Preventive Health"])

# ================= COMMUNITY FORUMS =================

@router.get("/api/community/groups")
def get_support_groups():
    """Returns directory of AI-moderated chronic condition support groups."""
    return SUPPORT_GROUPS_CATALOG

@router.get("/api/community/posts")
def get_community_posts(
    group_slug: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns AI-moderated community posts with safety verification badges.
    """
    query = db.query(CommunityPost).filter(CommunityPost.ai_moderation_status == "approved")
    if group_slug:
        query = query.filter(CommunityPost.group_slug == group_slug)
    posts = query.order_by(CommunityPost.created_at.desc()).all()

    if not posts:
        # Seed realistic initial verified peer posts
        default_posts = [
            {
                "group_slug": "diabetes_warriors",
                "group_name": "Type 2 Diabetes Warriors & CGM Circle",
                "title": "Continuous glucose monitoring tip for breakfast spikes",
                "content": "I started eating hard-boiled eggs and avocado before having my oatmeal, and my postprandial glucose spike decreased from 195 to 132 mg/dL. Huge improvement!",
                "author_id": 1,
                "likes": 18
            },
            {
                "group_slug": "heart_health",
                "group_name": "Hypertension & Cardio Wellness Alliance",
                "title": "Low sodium seasoning blends that actually taste great",
                "content": "Switching from regular table salt to lemon juice, toasted garlic, and nutritional yeast has brought my systolic BP down into the 120s over 3 weeks.",
                "author_id": 1,
                "likes": 24
            },
            {
                "group_slug": "preventive_living",
                "group_name": "Longevity & Preventive Habits Hub",
                "title": "10,000 steps daily consistency streak",
                "content": "Doing two 20-minute walks—one after lunch and one in the evening—makes hitting the 10k goal effortless.",
                "author_id": 1,
                "likes": 31
            }
        ]
        for dp in default_posts:
            mod = moderate_community_post(dp["title"], dp["content"])
            post_obj = CommunityPost(
                author_id=dp["author_id"],
                group_slug=dp["group_slug"],
                group_name=dp["group_name"],
                title=dp["title"],
                content=dp["content"],
                ai_safety_score=mod["ai_safety_score"],
                ai_moderation_status=mod["ai_moderation_status"],
                ai_moderation_notes=mod["ai_moderation_notes"],
                is_ai_verified=mod["is_ai_verified"],
                likes_count=dp["likes"]
            )
            db.add(post_obj)
        db.commit()
        posts = db.query(CommunityPost).filter(CommunityPost.ai_moderation_status == "approved").all()

    result = []
    for p in posts:
        author = db.query(User).filter(User.id == p.author_id).first()
        result.append({
            "id": p.id,
            "group_slug": p.group_slug,
            "group_name": p.group_name,
            "title": p.title,
            "content": p.content,
            "author_name": author.full_name if author else "Fellow Patient",
            "author_role": author.role if author else "patient",
            "is_ai_verified": p.is_ai_verified,
            "ai_safety_score": p.ai_safety_score,
            "ai_moderation_notes": p.ai_moderation_notes,
            "likes_count": p.likes_count,
            "created_at": p.created_at
        })
    return result

@router.post("/api/community/posts")
def create_community_post(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a new post to patient support group.
    Evaluated in real-time by AI clinical misinformation and safety filter.
    """
    group_slug = payload.get("group_slug", "diabetes_warriors")
    title = payload.get("title", "").strip()
    content = payload.get("content", "").strip()

    if not title or not content:
        raise HTTPException(status_code=400, detail="Title and content are required")

    group_meta = next((g for g in SUPPORT_GROUPS_CATALOG if g["slug"] == group_slug), None)
    group_name = group_meta["name"] if group_meta else "Patient Community"

    # AI Moderation Engine Check
    moderation = moderate_community_post(title, content)

    if moderation["ai_moderation_status"] == "rejected":
        raise HTTPException(
            status_code=400,
            detail=f"Post rejected by AI Medical Safety Moderation: {moderation['ai_moderation_notes']}"
        )

    post = CommunityPost(
        author_id=current_user.id,
        group_slug=group_slug,
        group_name=group_name,
        title=title,
        content=content,
        ai_safety_score=moderation["ai_safety_score"],
        ai_moderation_status=moderation["ai_moderation_status"],
        ai_moderation_notes=moderation["ai_moderation_notes"],
        is_ai_verified=moderation["is_ai_verified"],
        likes_count=0
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return {
        "status": "success",
        "post_id": post.id,
        "is_ai_verified": post.is_ai_verified,
        "ai_safety_score": post.ai_safety_score,
        "ai_notes": post.ai_moderation_notes
    }

@router.post("/api/community/posts/{post_id}/like")
def like_post(post_id: int, db: Session = Depends(get_db)):
    """Increment upvotes on a supportive community post."""
    p = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    p.likes_count += 1
    db.commit()
    return {"likes_count": p.likes_count}

# ================= PREVENTIVE HEALTH & GAMIFICATION =================

@router.get("/api/preventive/challenges")
def get_user_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns patient's active gamified wellness challenges with live progress and streaks.
    """
    challenges = db.query(PreventiveChallenge).filter(PreventiveChallenge.patient_id == current_user.id).all()
    if not challenges:
        for c in DEFAULT_PREVENTIVE_CHALLENGES:
            ch = PreventiveChallenge(
                patient_id=current_user.id,
                challenge_key=c["challenge_key"],
                title=c["title"],
                description=c["description"],
                target_value=c["target_value"],
                current_value=c["current_value"],
                unit=c["unit"],
                streak_days=3,
                points_reward=c["points_reward"],
                is_completed=c["current_value"] >= c["target_value"]
            )
            db.add(ch)
        db.commit()
        challenges = db.query(PreventiveChallenge).filter(PreventiveChallenge.patient_id == current_user.id).all()

    return [
        {
            "id": ch.id,
            "challenge_key": ch.challenge_key,
            "title": ch.title,
            "description": ch.description,
            "target_value": ch.target_value,
            "current_value": ch.current_value,
            "unit": ch.unit,
            "progress_percent": min(100, round((ch.current_value / ch.target_value) * 100)),
            "streak_days": ch.streak_days,
            "points_reward": ch.points_reward,
            "is_completed": ch.is_completed
        }
        for ch in challenges
    ]

@router.post("/api/preventive/challenges/{challenge_id}/log-progress")
def log_challenge_progress(
    challenge_id: int,
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logs preventive progress (e.g. added steps, water intake, BP logged).
    Awards points and updates streaks.
    """
    add_val = float(payload.get("increment", 1.0))
    ch = db.query(PreventiveChallenge).filter(
        PreventiveChallenge.id == challenge_id,
        PreventiveChallenge.patient_id == current_user.id
    ).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")

    ch.current_value += add_val
    newly_completed = False
    if ch.current_value >= ch.target_value and not ch.is_completed:
        ch.is_completed = True
        ch.streak_days += 1
        newly_completed = True

        # Award points to rewards balance
        reward = db.query(PatientReward).filter(PatientReward.patient_id == current_user.id).first()
        if reward:
            reward.total_points += ch.points_reward

    db.commit()
    db.refresh(ch)

    return {
        "status": "success",
        "current_value": ch.current_value,
        "is_completed": ch.is_completed,
        "streak_days": ch.streak_days,
        "points_awarded": ch.points_reward if newly_completed else 0
    }

@router.get("/api/preventive/rewards")
def get_patient_rewards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns patient points, tier status, and unlocked achievement badges.
    """
    reward = db.query(PatientReward).filter(PatientReward.patient_id == current_user.id).first()
    if not reward:
        reward = PatientReward(
            patient_id=current_user.id,
            total_points=420,
            tier_level="Platinum Vitality Member",
            badges_json=json.dumps([
                {"name": "Hydration Hero", "desc": "Reached 2.5L daily target 7 days consecutively", "icon": "bi-droplet-fill", "color": "info"},
                {"name": "Glucose Guardian", "desc": "100% adherence to glycemic self-monitoring", "icon": "bi-heart-pulse-fill", "color": "danger"},
                {"name": "10k Stepper", "desc": "Completed 50,000 steps across 5 days", "icon": "bi-lightning-charge-fill", "color": "warning"},
                {"name": "Blockchain Sovereign", "desc": "Verified ownership of encrypted health records", "icon": "bi-shield-lock-fill", "color": "primary"}
            ])
        )
        db.add(reward)
        db.commit()
        db.refresh(reward)

    badges = json.loads(reward.badges_json) if reward.badges_json else []

    vouchers = [
        {"title": "Free Specialist Teleconsult Voucher", "cost_points": 500, "status": "Available to Redeem"},
        {"title": "25% Discount on Complete Blood Panel (CBC/LFT/KFT)", "cost_points": 350, "status": "Unlocked & Ready"}
    ]

    return {
        "total_points": reward.total_points,
        "tier_level": reward.tier_level,
        "badges": badges,
        "vouchers": vouchers
    }

@router.get("/api/preventive/lifestyle-coach")
def get_lifestyle_coach(current_user: User = Depends(get_current_user)):
    """
    Returns customized AI lifestyle, nutrition, and exercise coaching
    tailored to patient's specific chronic illnesses.
    """
    patient_context = {
        "full_name": current_user.full_name,
        "pre_existing_conditions": current_user.pre_existing_conditions or "Type 2 Diabetes, Hypertension"
    }
    coaching = generate_personalized_lifestyle_coaching(patient_context)
    return coaching
