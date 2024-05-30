"""
This program sends messages read from a CSV file to a queue on the RabbitMQ server.
Adds logging instead of print statements for better visibility.

Author: Derek Graves
Date: May 31, 2024
"""

import pika
import csv
import sys
import webbrowser
import time
import traceback
from util_logger import setup_logger

# Set up logger
logger, logname = setup_logger(__file__)

# Configuration variables
HOST = "localhost"
QUEUE_NAMES = ["01-smoker", "02-food-A", "03-food-B"]
CSV_FILE = "smoker-temps.csv"
SHOW_OFFER = False
DELAY = 30  # Delay in seconds between sending tasks (30 for this assignment)

def offer_rabbitmq_admin_site():
    """Offer to open the RabbitMQ Admin website."""
    ans = input("Would you like to monitor RabbitMQ queues? y or n ")
    if ans.lower() == "y":
        webbrowser.open_new("http://localhost:15672/#/queues")
        print()

def connect_and_setup_queues(host):
    """
    Connect to RabbitMQ server, delete existing queues, and declare them anew.

    Parameters:
        host (str): the host name or IP address of the RabbitMQ server
    """
    try:
        # Create a blocking connection to the RabbitMQ server
        connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        channel = connection.channel()

        # Delete existing queues and declare them anew
        for queue_name in QUEUE_NAMES:
            channel.queue_delete(queue=queue_name)
            channel.queue_declare(queue=queue_name, durable=True)

        return connection, channel
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Connection to RabbitMQ server failed: {e}")
        sys.exit(1)

def send_message(channel, queue_name, message):
    """
    Publish a message to the specified queue.

    Parameters:
        channel: the communication channel to the RabbitMQ server
        queue_name (str): the name of the queue
        message (str): the message to be sent to the queue
    """
    try:
        channel.basic_publish(exchange="", routing_key=queue_name, body=message,
                              properties=pika.BasicProperties(delivery_mode=2))  # make message persistent
        logger.info(f"Sent {message} to {queue_name}")  # log the message sent to specific queue
    except Exception as e:
        logger.error(f"Error sending message to {queue_name}: {e}")

def process_csv_and_send_messages(filename, channel):
    """Read tasks from a CSV file and send messages to the appropriate queues."""
    try:
        with open(filename, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                timestamp = row['Time (UTC)']
                smoker_temp_str = row['Channel1']
                food_a_temp_str = row['Channel2']
                food_b_temp_str = row['Channel3']

                if smoker_temp_str:
                    smoker_temp = float(smoker_temp_str)
                    send_message(channel, "01-smoker", f"{timestamp}, {smoker_temp}")
                if food_a_temp_str:
                    food_a_temp = float(food_a_temp_str)
                    send_message(channel, "02-food-A", f"{timestamp}, {food_a_temp}")
                if food_b_temp_str:
                    food_b_temp = float(food_b_temp_str)
                    send_message(channel, "03-food-B", f"{timestamp}, {food_b_temp}")

                time.sleep(DELAY)  # Simulate sleep between messages 30 seconds
    except FileNotFoundError:
        logger.error(f"CSV file {filename} not found.")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Error processing CSV: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        traceback.print_exc()  # Print the traceback for detailed error information

if __name__ == "__main__":
    offer_rabbitmq_admin_site()

    # Get connection and channel
    connection, channel = connect_and_setup_queues(HOST)

    try:
        # Process CSV and send messages
        process_csv_and_send_messages(CSV_FILE, channel)
    finally:
        # Close the connection to the server
        if connection.is_open:
            connection.close()


