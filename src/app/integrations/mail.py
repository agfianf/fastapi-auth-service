import asyncio

import structlog

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from app.config import email_conf


logger = structlog.get_logger(__name__)


class MailSender:
    """Class to handle email sending."""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.fast_mail = FastMail(config)

    async def send_email_to(
        self,
        email: EmailStr,
        subject: str,
        body: str,
    ) -> None:
        """Send an email."""
        logger.debug("Sending email")
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=body,
            subtype=MessageType.html,
        )
        try:
            await self.fast_mail.send_message(message)
            logger.info("Email sent successfully")
        except Exception as e:
            logger.error("Failed to send email", error=str(e))
            raise e


if __name__ == "__main__":

    async def main():
        # Example usage
        mail_sender = MailSender(email_conf)
        try:
            await mail_sender.send_email_to(
                email="agfian@xxx.com",
                subject="Test Email",
                body="<h1>This is a test email</h1><p>Hello, this is a test email sent from FastAPI.</p>",
            )
        except Exception as e:
            logger.error("Error sending email", error=str(e))

    asyncio.run(main())
