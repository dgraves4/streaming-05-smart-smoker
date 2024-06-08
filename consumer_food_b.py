"""
Consumer for Food B Temperature.

This script reads messages from the "03-food-B" queue and processes them to detect temperature stalls.
Author: Derek Graves
Date: June 7, 2024
"""

import pika
import json
from collections import deque
import smtplib
from email.message import EmailMessage
import tomli  # Use tomli for reading TOML files
from util_logger import setup_logger  # Use util_logger for consistent logging

# Set up logger
logger, logname = setup_logger(__file__)

# Constants
QUEUE_NAME = '03-food-B'
DEQUE_MAX_LENGTH = 20  # 10 minutes worth of readings (20 * 30 seconds)
TEMPERATURE_CHANGE_THRESHOLD = 1  # Degrees Fahrenheit

# Load secrets from .env.toml
def load_secrets(file_path='.env.toml'):
    """Load secrets from the .env.toml file."""
    with open(file_path, 'rb') as f:
        return tomli.load(f)

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

    try:
        server = smtplib.SMTP(host, port)
        server.starttls()
        server.login(outemail, outpwd)
        server.send_message(msg)
        logger.info("Text alert sent successfully.")
    except smtplib.SMTPAuthenticationError:
        logger.error("Authentication error. Verify your email and password.")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        server.quit()

def food_b_callback(ch, method, properties, body):
    """Process messages from the food B queue."""
    message = body.decode()  # Decode the message body
    timestamp, temperature_str = message.split(', ')
    temperature = float(temperature_str)
    logger.info(f"Received temperature: {temperature}")

    # Add to deque and check for temperature stall
    temperature_readings.append(temperature)
    if len(temperature_readings) == DEQUE_MAX_LENGTH:
        temp_diff = max(temperature_readings) - min(temperature_readings)
        if temp_diff <= TEMPERATURE_CHANGE_THRESHOLD:
            alert_message = f"Food B Stall Alert! Temperature change ≤ 1°F at {timestamp}"
            logger.warning(alert_message)
            create_and_send_text_alert(alert_message)
        temperature_readings.popleft()

    # Acknowledge message
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    """Main function to set up RabbitMQ consumer."""
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare the queue
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    # Set up consumption of messages
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=food_b_callback, auto_ack=False)

    logger.info('Waiting for food B messages...')
    channel.start_consuming()

if __name__ == "__main__":
    # Deque for storing recent temperature readings
    temperature_readings = deque(maxlen=DEQUE_MAX_LENGTH)
    main()



