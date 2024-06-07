import smtplib
from email.message import EmailMessage
import tomllib  # Requires Python 3.11
import pprint

def load_secrets(file_path='.env.toml'):
    """Load secrets from the .env.toml file."""
    with open(file_path, 'rb') as f:
        config = tomllib.load(f)
    pprint.pprint(config)
    return config

def create_and_send_text_alert(text_message: str):
    """Send a text alert using the SMTP-to-SMS gateway."""
    secrets = load_secrets()
    host = secrets["outgoing_email_host"]
    port = secrets["outgoing_email_port"]
    outemail = secrets["outgoing_email_address"]
    outpwd = secrets["outgoing_email_password"]
    sms_address = secrets["sms_address_for_texts"]

    msg = EmailMessage()
    msg["From"] = outemail
    msg["To"] = sms_address
    msg.set_content(text_message)

    print("Prepared Email Message:")
    print(msg)

    try:
        server = smtplib.SMTP(host, port)
        server.starttls()
        server.login(outemail, outpwd)
        server.send_message(msg)
        print("Message sent.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.quit()

if __name__ == "__main__":
    msg = "Alert: This is a test message."
    create_and_send_text_alert(msg)
