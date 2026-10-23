"""
Database schema migration script for Dynamic Medical Passport & 1-Tap SOS upgrades.
Safely adds new columns using ALTER TABLE without altering existing records.
"""
import sqlite3
import os

DB_PATH = os.path.abspath("healthcare.db")

MIGRATIONS = [
    # Table: users
    ("users", "is_profile_verified", "BOOLEAN DEFAULT 0"),
    ("users", "profile_verified_at", "TIMESTAMP"),
    ("users", "profile_updated_at", "TIMESTAMP"),
    ("users", "emergency_contact_name", "VARCHAR(100)"),
    ("users", "emergency_contact_phone", "VARCHAR(30)"),

    # Table: emergency_access_audits
    ("emergency_access_audits", "status", "VARCHAR(30) DEFAULT 'SUCCESS'"),
    ("emergency_access_audits", "consent_status", "VARCHAR(30) DEFAULT 'GRANTED'"),
    ("emergency_access_audits", "expires_at", "TIMESTAMP"),
    ("emergency_access_audits", "revoked_at", "TIMESTAMP"),
    ("emergency_access_audits", "fields_viewed", "TEXT"),
    ("emergency_access_audits", "anomaly_detected", "BOOLEAN DEFAULT 0"),
    ("emergency_access_audits", "anomaly_reason", "VARCHAR(255)"),

    # Table: contextual_qr_tokens
    ("contextual_qr_tokens", "revoked_at", "TIMESTAMP"),
    ("contextual_qr_tokens", "required_role", "VARCHAR(50) DEFAULT 'public'"),
    ("contextual_qr_tokens", "authorized_by_pin", "VARCHAR(50)"),
    ("contextual_qr_tokens", "minute_request_count", "INTEGER DEFAULT 0"),
    ("contextual_qr_tokens", "last_rate_limit_reset", "TIMESTAMP"),

    # Table: caretaker_alert_configs
    ("caretaker_alert_configs", "alert_preference_sos", "BOOLEAN DEFAULT 1"),
    ("caretaker_alert_configs", "alert_preference_vitals", "BOOLEAN DEFAULT 1"),
    ("caretaker_alert_configs", "alert_preference_meds", "BOOLEAN DEFAULT 1"),
    ("caretaker_alert_configs", "secondary_name", "VARCHAR(100)"),
    ("caretaker_alert_configs", "secondary_phone", "VARCHAR(30)"),
    ("caretaker_alert_configs", "last_acknowledgement_at", "TIMESTAMP"),
    ("caretaker_alert_configs", "last_acknowledgement_status", "VARCHAR(100)"),

    # Table: emergency_alerts
    ("emergency_alerts", "incident_id", "VARCHAR(50)"),
    ("emergency_alerts", "idempotency_key", "VARCHAR(100)"),
    ("emergency_alerts", "delivery_status", "VARCHAR(50) DEFAULT 'QUEUED'"),
    ("emergency_alerts", "delivery_details", "TEXT"),
    ("emergency_alerts", "contacts_contacted", "TEXT"),
    ("emergency_alerts", "failure_fallback_triggered", "BOOLEAN DEFAULT 0"),
]

def run_migration():
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    applied_count = 0
    skipped_count = 0

    for table, column, col_type in MIGRATIONS:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not cursor.fetchone():
            print(f"[SKIP] Table '{table}' does not exist.")
            continue

        # Check existing columns
        cursor.execute(f"PRAGMA table_info({table})")
        existing_cols = [c[1] for c in cursor.fetchall()]

        if column in existing_cols:
            skipped_count += 1
            continue

        try:
            sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
            cursor.execute(sql)
            applied_count += 1
            print(f"[OK] Added {table}.{column} ({col_type})")
        except Exception as e:
            print(f"[ERROR] Failed to add {table}.{column}: {e}")

    conn.commit()
    conn.close()
    print(f"Migration completed: {applied_count} applied, {skipped_count} already existed.")

if __name__ == "__main__":
    run_migration()
