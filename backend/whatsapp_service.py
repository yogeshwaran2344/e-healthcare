"""
WhatsApp Messaging Service
Powered by Twilio WhatsApp API & Twilio Sandbox
Supports international E.164 phone normalization, Twilio error diagnostics,
and structured dispatch reporting for medication reminders & vital alerts.
"""

import os
import re
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger("WhatsAppService")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Load environment variables from possible locations
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent if _CURRENT_DIR.name == "backend" else _CURRENT_DIR
_ENV_PATHS = [
    _PROJECT_ROOT / ".env",
    _CURRENT_DIR / ".env",
    Path(".env")
]

for env_path in _ENV_PATHS:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
        break
else:
    load_dotenv()

# Twilio default Sandbox number
DEFAULT_SANDBOX_FROM = "whatsapp:+14155238886"


def sanitize_phone_number(phone: str) -> str:
    """
    Cleans and converts phone number into standardized E.164 international format.
    Handles Indian 10-digit mobile numbers (prepends +91), leading zeros, and symbols.
    Example:
        '86189 12755'      -> '+918618912755'
        '08618912755'      -> '+918618912755'
        '+91 86189-12755'  -> '+918618912755'
        '+1 (415) 5238886' -> '+14155238886'
    """
    if not phone:
        return ""
    
    # Strip any existing whatsapp: prefix for clean digit analysis
    raw = str(phone).strip()
    if raw.lower().startswith("whatsapp:"):
        raw = raw[9:].strip()

    # Retain leading '+' if present
    has_plus = raw.startswith("+")
    digits_only = re.sub(r"\D", "", raw)

    if not digits_only:
        return ""

    if has_plus:
        return f"+{digits_only}"

    # Default Indian mobile number normalization (10 digits)
    if len(digits_only) == 10:
        return f"+91{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith("0"):
        return f"+91{digits_only[1:]}"
    elif len(digits_only) == 12 and digits_only.startswith("91"):
        return f"+{digits_only}"
    
    return f"+{digits_only}"


def format_whatsapp_recipient(phone: str) -> str:
    """
    Ensures phone number has the required 'whatsapp:+<E.164>' prefix for Twilio.
    """
    e164 = sanitize_phone_number(phone)
    if not e164:
        return ""
    return f"whatsapp:{e164}"


def get_twilio_credentials(
    account_sid: Optional[str] = None,
    auth_token: Optional[str] = None,
    from_number: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    Resolves Twilio credentials from parameters or environment variables.
    """
    sid = (account_sid or os.getenv("TWILIO_ACCOUNT_SID", "")).strip().strip('"').strip("'")
    token = (auth_token or os.getenv("TWILIO_AUTH_TOKEN", "")).strip().strip('"').strip("'")
    from_val = (from_number or os.getenv("TWILIO_WHATSAPP_FROM", "")).strip().strip('"').strip("'")

    if not from_val:
        from_val = DEFAULT_SANDBOX_FROM
    elif not from_val.lower().startswith("whatsapp:"):
        from_val = f"whatsapp:{from_val}"

    return sid, token, from_val


def is_placeholder_credential(val: str) -> bool:
    """Checks if credential is an unconfigured example placeholder."""
    if not val:
        return True
    lowered = val.lower()
    return any(p in lowered for p in [
        "your_account_sid", "your_auth_token", "your_account", "placeholder",
        "xxxx", "ac00000", "00000000"
    ])


def send_whatsapp(
    phone_number: str,
    message: str,
    account_sid: Optional[str] = None,
    auth_token: Optional[str] = None,
    from_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends a WhatsApp message via Twilio API.
    
    Parameters:
        phone_number: Recipient's mobile number (e.g. '+918618912755' or '8618912755')
        message: Text body of the WhatsApp message
        account_sid: Optional Twilio Account SID override
        auth_token: Optional Twilio Auth Token override
        from_number: Optional Twilio WhatsApp sender override (e.g. 'whatsapp:+14155238886')

    Returns:
        Structured response dictionary with success status, SID, and diagnostic details.
    """
    to_formatted = format_whatsapp_recipient(phone_number)
    sid, token, from_formatted = get_twilio_credentials(account_sid, auth_token, from_number)

    if not to_formatted:
        error_msg = f"Invalid recipient phone number format: '{phone_number}'"
        logger.error(error_msg)
        return {
            "success": False,
            "sid": None,
            "status": "failed",
            "to": phone_number,
            "from": from_formatted,
            "error": error_msg,
            "help_tip": "Provide an international mobile number with country code, e.g. +91 98765 43210."
        }

    if not message or not message.strip():
        error_msg = "Message content cannot be empty."
        logger.error(error_msg)
        return {
            "success": False,
            "sid": None,
            "status": "failed",
            "to": to_formatted,
            "from": from_formatted,
            "error": error_msg,
            "help_tip": "Provide non-empty text body for the notification."
        }

    import urllib.parse
    clean_e164 = sanitize_phone_number(phone_number)
    digits_only = clean_e164.replace("+", "")
    encoded_body = urllib.parse.quote(message)
    direct_wa_url = f"https://api.whatsapp.com/send?phone={digits_only}&text={encoded_body}"
    direct_sms_url = f"sms:{clean_e164}?body={encoded_body}"

    # Verify Twilio credentials
    if is_placeholder_credential(sid) or is_placeholder_credential(token):
        tip = (
            "Twilio credentials not configured. In your .env file or environment, set:\n"
            "TWILIO_ACCOUNT_SID=your_actual_sid\n"
            "TWILIO_AUTH_TOKEN=your_actual_auth_token\n"
            "TWILIO_WHATSAPP_FROM=whatsapp:+17372508034\n"
            "Get free test credentials at https://www.twilio.com/try-twilio"
        )
        logger.warning(f"Twilio credentials missing or placeholder. Message simulated to {to_formatted}.")
        return {
            "success": False,
            "simulated": True,
            "sid": "SIMULATED_NO_CREDENTIALS",
            "status": "credentials_required",
            "to": to_formatted,
            "from": from_formatted,
            "message_preview": message[:100] + ("..." if len(message) > 100 else ""),
            "direct_whatsapp_url": direct_wa_url,
            "direct_sms_url": direct_sms_url,
            "error": "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be configured in .env",
            "help_tip": tip
        }

    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException

        client = Client(sid, token)
        result = client.messages.create(
            from_=from_formatted,
            to=to_formatted,
            body=message
        )

        logger.info(f"WhatsApp message dispatched to {to_formatted}. SID: {result.sid}, Status: {result.status}")
        return {
            "success": True,
            "sid": result.sid,
            "status": result.status,
            "to": to_formatted,
            "from": from_formatted,
            "direct_whatsapp_url": direct_wa_url,
            "direct_sms_url": direct_sms_url,
            "error": None,
            "date_created": str(getattr(result, "date_created", "")),
            "help_tip": None
        }

    except TwilioRestException as error:
        code = getattr(error, "code", None)
        msg = getattr(error, "msg", str(error))
        help_tip = None

        if code == 21608:
            help_tip = (
                f"Twilio WhatsApp Sandbox Enrollment Required: Recipient {to_formatted} has not joined your Sandbox. "
                f"On the recipient's phone, open WhatsApp, message {from_formatted.replace('whatsapp:', '')}, "
                f"and send your sandbox joining code (found in Twilio Console -> Messaging -> Try WhatsApp). "
                f"Alternatively, click the Direct WhatsApp link below to dispatch directly."
            )
        elif code == 20003:
            help_tip = "Twilio Authentication Error: Your TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN is invalid. Verify them in Twilio Console."
        elif code == 21211:
            help_tip = f"Invalid 'To' number: {to_formatted}. Verify country code and phone digits."
        elif code == 21654:
            clean_from = from_formatted.replace("whatsapp:", "")
            help_tip = (
                f"WhatsApp 24-Hour Session Window Required: Outside an active 24-hour conversation window, WhatsApp prevents freeform outbound messages. "
                f"To re-open the window, open WhatsApp on the recipient's phone ({to_formatted}), "
                f"send a quick message (e.g. 'join twilio-trial' or 'Hi') to your Twilio number {clean_from}. "
                f"Alternatively, click the Direct WhatsApp link to send to any mobile number instantly!"
            )

        logger.error(f"Twilio WhatsApp Error ({code}): {msg}")
        return {
            "success": False,
            "sid": None,
            "status": "failed",
            "error_code": code,
            "to": to_formatted,
            "from": from_formatted,
            "direct_whatsapp_url": direct_wa_url,
            "direct_sms_url": direct_sms_url,
            "error": msg,
            "help_tip": help_tip or "Check your Twilio console logs for delivery status."
        }

    except Exception as general_error:
        logger.error(f"Unexpected WhatsApp error: {general_error}")
        return {
            "success": False,
            "sid": None,
            "status": "error",
            "to": to_formatted,
            "from": from_formatted,
            "direct_whatsapp_url": direct_wa_url,
            "direct_sms_url": direct_sms_url,
            "error": str(general_error),
            "help_tip": "Ensure python packages 'twilio' and 'python-dotenv' are installed."
        }


def check_whatsapp_service_health() -> Dict[str, Any]:
    """Returns diagnostics on the current Twilio WhatsApp setup."""
    sid, token, from_num = get_twilio_credentials()
    has_sid = not is_placeholder_credential(sid)
    has_token = not is_placeholder_credential(token)
    
    return {
        "status": "configured" if (has_sid and has_token) else "unconfigured",
        "has_account_sid": has_sid,
        "has_auth_token": has_token,
        "from_sender": from_num,
        "is_sandbox": "+14155238886" in from_num,
        "instructions": (
            "To send live WhatsApp messages: 1) Sign up at twilio.com, 2) Join Sandbox by texting the join code to +1 415 523 8886, "
            "3) Put TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env."
        )
    }
