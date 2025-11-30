from google.adk.tools.agent_tool import AgentTool
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


class BrevoEmailTool(AgentTool):
    """
    Email-sending tool that uses Brevo SMTP relay.
    """

    def __init__(self):
        super().__init__(
            name="brevo_email_tool",
            description="Send an email using Brevo SMTP relay",
            parameters={
                "to": {"type": "string", "description": "Recipient email"},
                "subject": {"type": "string", "description": "Email subject"},
                "message": {"type": "string", "description": "Plain text message"},
                "from_email": {
                    "type": "string",
                    "description": "Sender email",
                    "optional": True,
                },
            },
        )

        # SMTP credentials from env
        self.smtp_user = os.getenv("BREVO_SMTP_USER")
        self.smtp_key = os.getenv("BREVO_SMTP_KEY")

    def run(self, to, subject, message, from_email=None, **kwargs):
        """
        Execute the email sending.
        """

        from_email = from_email or self.smtp_user

        # SMTP server settings
        smtp_host = "smtp-relay.brevo.com"
        smtp_port = 587

        # Build email
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        try:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_key)
            server.sendmail(from_email, to, msg.as_string())
            server.quit()

            return {"status": "success", "message": f"Email sent to {to}"}

        except Exception as e:
            return {"status": "error", "error": str(e)}
