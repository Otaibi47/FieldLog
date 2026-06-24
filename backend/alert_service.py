import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Equipment

logger = logging.getLogger(__name__)

ALERT_EMAIL_RECIPIENT = os.getenv("ALERT_EMAIL_RECIPIENT", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "alerts@fieldlog.app")


async def get_overdue_equipment(db: AsyncSession) -> list[Equipment]:
    today = date.today()
    result = await db.execute(
        select(Equipment).where(Equipment.next_maintenance_due < today)
    )
    return result.scalars().all()


async def send_overdue_alert_email(overdue_items: list[Equipment]):
    if not overdue_items or not ALERT_EMAIL_RECIPIENT:
        return

    today = date.today()
    rows = ""
    for item in overdue_items:
        days = (today - item.next_maintenance_due).days
        last = item.last_maintenance_date.isoformat() if item.last_maintenance_date else "N/A"
        rows += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #eee">{item.name}</td>
            <td style="padding:8px;border-bottom:1px solid #eee">{item.location}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;color:#DC2626;font-weight:bold">{days} days</td>
            <td style="padding:8px;border-bottom:1px solid #eee">{last}</td>
        </tr>"""

    html = f"""
    <html><body style="font-family:Segoe UI,sans-serif;color:#111827">
    <h2 style="color:#DC2626">FieldLog — Overdue Maintenance Alert</h2>
    <p>{len(overdue_items)} equipment item(s) require immediate attention.</p>
    <table style="border-collapse:collapse;width:100%">
        <thead><tr style="background:#F3F4F6">
            <th style="padding:8px;text-align:left">Equipment</th>
            <th style="padding:8px;text-align:left">Location</th>
            <th style="padding:8px;text-align:left">Days Overdue</th>
            <th style="padding:8px;text-align:left">Last Maintained</th>
        </tr></thead>
        <tbody>{rows}</tbody>
    </table>
    <p style="color:#6B7280;font-size:12px;margin-top:24px">Sent by FieldLog alert service</p>
    </body></html>"""

    if SENDGRID_API_KEY:
        await _send_via_sendgrid(html)
    else:
        _send_via_smtp(html)


async def _send_via_sendgrid(html: str):
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"},
                json={
                    "personalizations": [{"to": [{"email": ALERT_EMAIL_RECIPIENT}]}],
                    "from": {"email": SENDER_EMAIL},
                    "subject": "FieldLog — Overdue Maintenance Alert",
                    "content": [{"type": "text/html", "value": html}],
                },
            )
            if resp.status_code not in (200, 202):
                logger.error("SendGrid error: %s", resp.text)
    except Exception as e:
        logger.error("Failed to send alert email via SendGrid: %s", e)


def _send_via_smtp(html: str):
    smtp_host = os.getenv("SMTP_HOST", "localhost")
    smtp_port = int(os.getenv("SMTP_PORT", "25"))
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "FieldLog — Overdue Maintenance Alert"
        msg["From"] = SENDER_EMAIL
        msg["To"] = ALERT_EMAIL_RECIPIENT
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.sendmail(SENDER_EMAIL, ALERT_EMAIL_RECIPIENT, msg.as_string())
    except Exception as e:
        logger.error("Failed to send alert email via SMTP: %s", e)


async def run_alert_check(db: AsyncSession):
    overdue = await get_overdue_equipment(db)
    if overdue:
        logger.info("Alert check: %d overdue items found", len(overdue))
        await send_overdue_alert_email(overdue)
    else:
        logger.info("Alert check: no overdue items")
