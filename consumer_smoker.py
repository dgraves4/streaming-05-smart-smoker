"""
Consumer for Smoker Temperature.

This script reads messages from the "01-smoker" queue and processes them to detect significant temperature drops.
Author: Derek Graves
Date: June 7, 2024
"""

import pika
import json
from collections import deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
QUEUE_NAME = '01-smoker'
DEQUE_MAX_LENGTH = 5  # 2.5 minutes worth of readings (5 * 30 seconds)
TEMPERATURE_DROP_THRESHOLD = 15  # Degrees Fahrenheit

def smoker_callback(ch, method, properties, body):
    """Process messages from the smoker queue."""
    message = json.loads(body)
    temperature = message.get('temperature')
    logger.info(f"Received temperature: {temperature}")

    # Add to deque and check for temperature drop
    temperature_readings.append(temperature)
    if len(temperature_readings) == DEQUE_MAX_LENGTH:
        temp_diff = temperature_readings[0] - temperature_readings[-1]
        if temp_diff >= TEMPERATURE_DROP_THRESHOLD:
            logger.warning(f"Smoker Alert! Temperature dropped by {temp_diff}°F")
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
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=smoker_callback, auto_ack=False)

    logger.info('Waiting for smoker messages...')
    channel.start_consuming()

if __name__ == "__main__":
    # Deque for storing recent temperature readings
    temperature_readings = deque(maxlen=DEQUE_MAX_LENGTH)
    main()
