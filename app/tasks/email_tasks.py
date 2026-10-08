import logging
import mimetypes
import smtplib
from email.message import EmailMessage

from fastapi import BackgroundTasks

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def send_notification_email(background_tasks: BackgroundTasks, recipient: str, subject: str, message: str, attachments: list[dict] | None = None) -> None:
    background_tasks.add_task(_send_email, recipient, subject, message, attachments or [])


def _build_message(recipient: str, subject: str, message: str, attachments: list[dict]) -> EmailMessage:
    email = EmailMessage()
    email["From"] = settings.smtp_from or settings.smtp_user
    email["To"] = recipient
    email["Subject"] = subject
    email.set_content(message)
    for attachment in attachments:
        filename = attachment.get("filename", "piece-jointe")
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        maintype, subtype = content_type.split("/", 1)
        email.add_attachment(attachment["content"], maintype=maintype, subtype=subtype, filename=filename)
    return email


def _send_email(recipient: str, subject: str, message: str, attachments: list[dict]) -> None:
    if not settings.smtp_host:
        # SMTP non configuré (dev/tests) : on affiche l'email dans la console.
        print(f"[Email] À: {recipient}, sujet: {subject}")
        print(message)
        for attachment in attachments:
            print(f"Attachment: {attachment.get('filename')}")
        return

    email = _build_message(recipient, subject, message, attachments)
    try:
        if settings.smtp_use_ssl:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20)
        with server:
            if not settings.smtp_use_ssl and settings.smtp_starttls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password or "")
            server.send_message(email)
    except (smtplib.SMTPException, OSError):
        # L'envoi tourne en tâche de fond : on journalise sans faire échouer la requête.
        logger.exception("Échec de l'envoi de l'email à %s (sujet: %s)", recipient, subject)
