"""
This program sends messages read from a CSV file to a queue on the RabbitMQ server.
Adds logging instead of print statements for better visibility.

Author: Derek Graves
Date: May 24, 2024
"""

import pika
import csv
import sys
import webbrowser
import time
from util_logger import setup_logger

# Set up logger
logger, logname = setup_logger(__file__)

# Configuration variables
HOST = "localhost"
QUEUE_NAMES = ["01-smoker", "02-food-A", "03-food-B"]
CSV_FILE = "smoker-temps.csv"
SHOW_OFFER = False
DELAY = 30  # Delay in seconds between sending tasks (30 for this assignment)

def offer_rabbitmq_admin_site(show_offer=True):
    """Offer to open the RabbitMQ Admin website"""
    if show_offer:
        ans = input("Would you like to monitor RabbitMQ queues? y or n ")
        if ans.lower() == "y":
            webbrowser.open_new("http://localhost:15672/#/queues")

def send_message(host: str, queue_name: str, message: str):
    """
    Creates and sends a message to the queue each execution.
    This process runs and finishes.

    Parameters:
        host (str): the host name or IP address of the RabbitMQ server
        queue_name (str): the name of the queue
        message (str): the message to be sent to the queue
    """
    try:
        # create a blocking connection to the RabbitMQ server
        conn = pika.BlockingConnection(pika.ConnectionParameters(host))
        # use the connection to create a communication channel
        ch = conn.channel()
        # use the channel to declare a durable queue
        ch.queue_declare(queue=queue_name, durable=True)
        # use the channel to publish a message to the queue
        ch.basic_publish(exchange="", routing_key=queue_name, body=message,
                         properties=pika.BasicProperties(delivery_mode=2))  # make message persistent
        logger.info(f"Sent {message} to {queue_name}") # log the message sent to specific queue
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Connection to RabbitMQ server failed: {e}")
        sys.exit(1)
    finally:
        # close the connection to the server
        if conn.is_open:
            conn.close()

def read_tasks_from_csv(filename=CSV_FILE):
    """Read tasks from a CSV file and return a list of tasks"""
    tasks = []
    try:
        with open(filename, newline='') as csvfile:
            task_reader = csv.DictReader(csvfile)
            for row in task_reader:
                tasks.append({
                    "timestamp": row["Time"]
                    "smoker_temp": row["Channel1"]
                    "food_a_temp": row["Channel2"]
                    "food_b_temp": row["Channel3"]
                })
    except FileNotFoundError:
        logger.error(f"File {filename} not found.")
        sys.exit(1)
    return tasks

if __name__ == "__main__":
    offer_rabbitmq_admin_site(SHOW_OFFER)

    # Read tasks from the CSV file
    tasks = read_tasks_from_csv()

    # Send each task to the queue
    for task in tasks:
        send_message(HOST, "01-smoker", f"task['timestamp'] task['smoker_temp']")
        send_message(HOST, "02-food-A", f"task['timestamp'] task['food_a_temp']")
        send_message(HOST, "03-food-B", f"task['timestamp'] task['food_b_temp']")
        time.sleep(DELAY) #Simulate sleep between messages 30 seconds

