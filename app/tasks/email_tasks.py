from fastapi import BackgroundTasks


def send_notification_email(background_tasks: BackgroundTasks, recipient: str, subject: str, message: str, attachments: list[dict] | None = None) -> None:
    background_tasks.add_task(_send_email, recipient, subject, message, attachments or [])


def _send_email(recipient: str, subject: str, message: str, attachments: list[dict]) -> None:
    # Stubbed email delivery. Replace avec un service SMTP/Celery dans la suite.
    print(f"[Email] À: {recipient}, sujet: {subject}")
    print(message)
    for attachment in attachments:
        print(f"Attachment: {attachment.get('filename')}")
