"""
Consumer for Food B Temperature.

This script reads messages from the "03-food-B" queue and processes them to detect temperature stalls.
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
QUEUE_NAME = '03-food-B'
DEQUE_MAX_LENGTH = 20  # 10 minutes worth of readings (20 * 30 seconds)
TEMPERATURE_CHANGE_THRESHOLD = 1  # Degrees Fahrenheit

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
            logger.warning("Food B Stall Alert! Temperature change ≤ 1°F")
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

