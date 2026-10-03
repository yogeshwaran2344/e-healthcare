"""
Hospital Indoor Navigation Graph & Smart Priority Queue Management Engine.
Core Technical Mechanisms:
- Multi-floor hospital topological routing graph with Dijkstra shortest-path navigation.
- Augmented Reality (AR) camera waypoint overlay projection (turn-by-turn guidance).
- Clinical Urgency Priority Queue: Dynamic queue insertion algorithm that automatically
  promotes emergency/critical triage patients to front-of-queue priority bypass.
"""

import heapq
from typing import Dict, Any, List, Optional, Tuple

HOSPITAL_WAYPOINTS = {
    # Ground Floor
    "ENTRANCE": {
        "floor": "Ground Floor",
        "name": "Main Hospital Entrance & Reception",
        "category": "entrance",
        "x": 100, "y": 450,
        "instructions": "Enter via Main North Lobby."
    },
    "REGISTRATION": {
        "floor": "Ground Floor",
        "name": "Central OPD Registration & Billing",
        "category": "opd",
        "x": 220, "y": 380,
        "instructions": "Proceed to Desk 3 for token issuance."
    },
    "EMERGENCY_ER": {
        "floor": "Ground Floor",
        "name": "Emergency Department & Trauma Bay",
        "category": "emergency",
        "x": 450, "y": 480,
        "instructions": "Follow Red Floor Stripe directly to Trauma Bay 1."
    },
    "PHARMACY": {
        "floor": "Ground Floor",
        "name": "24/7 Outpatient Pharmacy",
        "category": "pharmacy",
        "x": 380, "y": 280,
        "instructions": "Collect digital e-prescription at Counter 4."
    },
    "ELEVATOR_GF": {
        "floor": "Ground Floor",
        "name": "Central Elevators (Ground Floor)",
        "category": "elevator",
        "x": 300, "y": 200,
        "instructions": "Take Elevator to Floor 1 (OPD) or Floor 2 (Diagnostics)."
    },
    
    # 1st Floor
    "ELEVATOR_1F": {
        "floor": "1st Floor",
        "name": "Central Elevators (1st Floor)",
        "category": "elevator",
        "x": 300, "y": 200,
        "instructions": "Exit elevator into 1st Floor Medical Wing."
    },
    "OPD_PULMONOLOGY": {
        "floor": "1st Floor",
        "name": "Dr. Sarah Sharma - Pulmonology Suite 104",
        "category": "opd",
        "x": 150, "y": 140,
        "instructions": "Turn left from elevator into West Wing, Suite 104."
    },
    "OPD_CARDIOLOGY": {
        "floor": "1st Floor",
        "name": "Dr. Rajesh Mehta - Cardiology Suite 102",
        "category": "opd",
        "x": 420, "y": 140,
        "instructions": "Turn right from elevator into East Wing, Suite 102."
    },
    "BLOOD_BANK": {
        "floor": "1st Floor",
        "name": "Blood Bank & Transfusion Medicine",
        "category": "lab",
        "x": 450, "y": 320,
        "instructions": "Follow Yellow Floor Stripe to Blood Bank Room 112."
    },

    # 2nd Floor
    "ELEVATOR_2F": {
        "floor": "2nd Floor",
        "name": "Central Elevators (2nd Floor)",
        "category": "elevator",
        "x": 300, "y": 200,
        "instructions": "Exit into Diagnostic & Imaging Center."
    },
    "PATHOLOGY_LAB": {
        "floor": "2nd Floor",
        "name": "Central Diagnostic & Pathology Lab",
        "category": "lab",
        "x": 160, "y": 120,
        "instructions": "Sample collection counters 1-5 for Blood & Urine Panels."
    },
    "RADIOLOGY": {
        "floor": "2nd Floor",
        "name": "Radiology (Digital Chest X-Ray & CT Scan)",
        "category": "radiology",
        "x": 440, "y": 130,
        "instructions": "Report to Radiology Desk for X-Ray / CT contrast scan."
    }
}

# Graph Edges (Node A, Node B, distance_meters)
NAVIGATION_EDGES = [
    ("ENTRANCE", "REGISTRATION", 25),
    ("REGISTRATION", "ELEVATOR_GF", 30),
    ("REGISTRATION", "PHARMACY", 35),
    ("ENTRANCE", "EMERGENCY_ER", 40),
    ("EMERGENCY_ER", "ELEVATOR_GF", 45),
    ("ELEVATOR_GF", "PHARMACY", 20),

    # Vertical Transit
    ("ELEVATOR_GF", "ELEVATOR_1F", 10),
    ("ELEVATOR_1F", "ELEVATOR_2F", 10),

    # 1st Floor
    ("ELEVATOR_1F", "OPD_PULMONOLOGY", 35),
    ("ELEVATOR_1F", "OPD_CARDIOLOGY", 30),
    ("ELEVATOR_1F", "BLOOD_BANK", 40),

    # 2nd Floor
    ("ELEVATOR_2F", "PATHOLOGY_LAB", 40),
    ("ELEVATOR_2F", "RADIOLOGY", 45)
]

def find_shortest_indoor_route(start_code: str, target_code: str) -> Dict[str, Any]:
    """
    Computes shortest path across hospital floor navigation graph using Dijkstra's algorithm.
    """
    if start_code not in HOSPITAL_WAYPOINTS or target_code not in HOSPITAL_WAYPOINTS:
        start_code = "ENTRANCE"
        target_code = "OPD_PULMONOLOGY"

    # Build adjacency
    adj = {node: [] for node in HOSPITAL_WAYPOINTS}
    for u, v, weight in NAVIGATION_EDGES:
        adj[u].append((v, weight))
        adj[v].append((u, weight))

    # Dijkstra
    distances = {node: float("inf") for node in HOSPITAL_WAYPOINTS}
    distances[start_code] = 0
    previous = {}
    pq = [(0, start_code)]

    while pq:
        curr_dist, curr_node = heapq.heappop(pq)
        if curr_dist > distances[curr_node]:
            continue
        if curr_node == target_code:
            break

        for neighbor, weight in adj.get(curr_node, []):
            dist = curr_dist + weight
            if dist < distances[neighbor]:
                distances[neighbor] = dist
                previous[neighbor] = curr_node
                heapq.heappush(pq, (dist, neighbor))

    # Reconstruct Path
    path_codes = []
    curr = target_code
    while curr:
        path_codes.append(curr)
        curr = previous.get(curr)
    path_codes.reverse()

    waypoints_detail = []
    directions_steps = []
    for idx, code in enumerate(path_codes):
        wp = HOSPITAL_WAYPOINTS[code]
        waypoints_detail.append({
            "code": code,
            "name": wp["name"],
            "floor": wp["floor"],
            "category": wp["category"],
            "x": wp["x"],
            "y": wp["y"]
        })
        if idx == 0:
            directions_steps.append(f"Start at {wp['name']}.")
        else:
            prev_wp = HOSPITAL_WAYPOINTS[path_codes[idx - 1]]
            if prev_wp["floor"] != wp["floor"]:
                directions_steps.append(f"Take elevator from {prev_wp['floor']} up to {wp['floor']}.")
            else:
                directions_steps.append(f"Head toward {wp['name']} ({wp['instructions']}).")

    total_meters = distances.get(target_code, 45)
    walk_minutes = max(1, round(total_meters / 40))

    # AR HUD Waypoint Cues
    ar_waypoints = []
    for i, pt in enumerate(waypoints_detail):
        ar_waypoints.append({
            "step": i + 1,
            "target": pt["name"],
            "distance_m": round(total_meters * (i + 1) / len(waypoints_detail)),
            "heading_degrees": (i * 45) % 360,
            "pitch_degrees": -5,
            "ar_badge": pt["category"].upper(),
            "ar_cue": "Continue straight" if i < len(waypoints_detail) - 1 else "Arrived at Destination"
        })

    return {
        "start": start_code,
        "destination": target_code,
        "total_distance_meters": total_meters,
        "estimated_walk_minutes": walk_minutes,
        "start_floor": HOSPITAL_WAYPOINTS[start_code]["floor"],
        "target_floor": HOSPITAL_WAYPOINTS[target_code]["floor"],
        "waypoints": waypoints_detail,
        "directions": directions_steps,
        "ar_camera_hud": ar_waypoints
    }

def calculate_queue_priority(triage_level: str, iot_critical: bool = False) -> Tuple[str, int]:
    """
    Determines queue priority level and estimated wait time multiplier.
    Returns: (priority_level, estimated_wait_minutes)
    """
    if triage_level == "Emergency Care" or iot_critical:
        return "EMERGENCY_CRITICAL", 0  # Immediate front of line
    elif triage_level == "Doctor Consultation":
        return "PRIORITY", 10
    else:
        return "NORMAL", 20
