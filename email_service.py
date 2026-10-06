"""
email_service.py
Composes and sends "your vehicle needs servicing" emails to customers
whose vehicles are OVERDUE or DUE SOON.

Safe by design: if email_config.py isn't filled in (ENABLED = False),
nothing is actually sent over the network -- the composed email is
written to sent_emails_log.txt instead, so the feature is still fully
demonstrable without real credentials.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path

import email_config as cfg

LOG_PATH = Path(__file__).parent / "sent_emails_log.txt"

REMINDER_STATUSES = ("OVERDUE", "DUE SOON")


def is_configured() -> bool:
    return bool(cfg.ENABLED and cfg.SMTP_USERNAME and cfg.SMTP_PASSWORD)


def group_reminders_needing_email(all_reminders):
    """
    Filter admin-wide reminders down to OVERDUE/DUE SOON ones, and group
    them by customer so each customer gets ONE consolidated email even
    if they have several vehicles needing attention.
    Returns: {user_id: {"full_name":.., "email":.., "reminders": [...]}}
    """
    grouped = {}
    for r in all_reminders:
        if r["status"] not in REMINDER_STATUSES:
            continue
        if not r.get("owner_email"):
            continue  # can't email a customer with no email on file
        uid = r["user_id"]
        if uid not in grouped:
            grouped[uid] = {
                "full_name": r["owner_full_name"],
                "email": r["owner_email"],
                "reminders": [],
            }
        grouped[uid]["reminders"].append(r)
    return grouped


def build_message(customer_name: str, to_email: str, reminders: list) -> MIMEText:
    lines = [
        f"Dear {customer_name},",
        "",
        "This is an automated reminder from the Two-Wheeler Service Reminder Manager. "
        "The following vehicle(s) registered to your account need servicing attention:",
        "",
    ]
    for r in reminders:
        lines.append(f"- {r['label']} -- status: {r['status']}")
        if r["next_service_date"]:
            lines.append(f"    Calendar due date: {r['next_service_date']}")
        if r["next_service_odometer"] is not None:
            lines.append(f"    Due odometer: {r['next_service_odometer']} km "
                         f"(km remaining: {r['km_remaining']})")
        if r["smart_eta"]:
            lines.append(f"    Smart ETA (usage-based prediction): {r['smart_eta']} "
                         f"[{r['smart_basis']}]")
        lines.append("")
    lines += [
        "Please book a service appointment at your earliest convenience.",
        "",
        "-- Two-Wheeler Service Reminder Manager (automated message)",
    ]
    body = "\n".join(lines)

    msg = MIMEText(body, "plain")
    msg["Subject"] = f"Service Reminder: {len(reminders)} vehicle(s) need attention"
    msg["From"] = f"{cfg.SENDER_NAME} <{cfg.SMTP_USERNAME or 'no-reply@example.com'}>"
    msg["To"] = to_email
    return msg


def _append_log(customer_name, to_email, msg, sent_status):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write(f"Timestamp : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Status    : {sent_status}\n")
        f.write(f"Customer  : {customer_name} <{to_email}>\n")
        f.write("-" * 70 + "\n")
        f.write(msg.get_payload())
        f.write("\n\n")


def _send_via_smtp(msg) -> tuple[bool, str]:
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=15) as server:
            server.starttls(context=context)
            server.login(cfg.SMTP_USERNAME, cfg.SMTP_PASSWORD)
            server.send_message(msg)
        return True, "Sent"
    except Exception as exc:
        return False, f"Failed: {exc}"


def send_reminder_emails(all_reminders):
    """
    Main entry point used by the Admin > Email Center screen.
    Returns a list of per-customer result dicts for display:
        {"customer": name, "email": email, "vehicle_count": n,
         "outcome": "Sent" | "Dry-run (logged)" | "Failed: ..."}
    """
    grouped = group_reminders_needing_email(all_reminders)
    results = []
    for uid, info in grouped.items():
        msg = build_message(info["full_name"], info["email"], info["reminders"])
        if is_configured():
            ok, outcome = _send_via_smtp(msg)
            _append_log(info["full_name"], info["email"], msg,
                        "SENT" if ok else f"SEND FAILED ({outcome})")
        else:
            ok, outcome = False, "Dry-run (logged, not sent -- fill in email_config.py to send for real)"
            _append_log(info["full_name"], info["email"], msg, "DRY RUN")
        results.append({
            "customer": info["full_name"],
            "email": info["email"],
            "vehicle_count": len(info["reminders"]),
            "outcome": outcome,
        })
    return results
