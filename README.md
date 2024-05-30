# streaming-05-smart-smoker
This project simulates a streaming data producer for a "smart smoker" system. It reads temperature data from a CSV file and sends it to specified RabbitMQ queues at regular intervals. The system monitors and reports the temperatures of the smoker and the food items being cooked.

The script performs the following tasks:

1. Connects to a RabbitMQ server.
2. Deletes existing queues (if any) and declares new ones.
3. Reads temperature data from a CSV file.
4. Publishes the temperature data to the appropriate RabbitMQ queues at 30-second intervals.
5. Logs all operations for better visibility and debugging.

## Author

- Derek Graves
- May 31, 2024

## Prior to Beginning

1. Fork starter repo into GitHub.
2. Clone repo down to machine.
3. In VS Code, select python interpreter:
- View > Command Palette

## Setup 

1. Use previous emitter file V3 as template and copy to root project folder: https://github.com/dgraves4/streaming-04-multiple-consumers/blob/main/v3_emitter_of_tasks.py. Rename bbq_producer_v1.0.

2. Create virtual environment:
```bash
py -m venv .venv
```
3.  Activate environment:
```bash
source .venv/scripts/activate
```
4.  Install external packages:
```bash
pip install pika
```
or you can install from 'requirements.txt':

```bash
pip install -r requirements.txt
```

5. Rabbit MQ Installation
- Follow instructions on [RabbitMQ Installation](https://www.rabbitmq.com/tutorials) to install RabbitMQ.
- Ensure the RabbitMQ server is running on your machine once installed.

6. Add additional files:
- Add a .gitignore file (copied from earlier module) https://github.com/dgraves4/streaming-04-multiple-consumers/blob/main/.gitignore.
- Add CSV data file to root project folder 'smoker-temps.csv'.

## Directory Structure
```bash
streaming-05-smart-smoker/
├── .venv/
├── .gitignore
├── bbq_producer_v1.0.py
├── requirements.txt
├── smoker-temps.csv
├── util_logger.py
└── README.md
```
## Design and Implement Producer
- Copy util_logger.py into project folder if you wish to use the logging utility.
- Create producer script:
1. Start with useful docstring at the top of file and include Author name and Date.
2. List imports needed for the script.
3. Declare all  constants such as 'HOST', 'QUEUE_NAMES', 'CSV_FILE', and 'DELAY'.
4. Define all functions:
- 'offer_rabbitmq_admin_site()'
```bash
def offer_rabbitmq_admin_site():
    """Offer to open the RabbitMQ Admin website."""
    ans = input("Would you like to monitor RabbitMQ queues? y or n ")
    if ans.lower() == "y":
        webbrowser.open_new("http://localhost:15672/#/queues")
        logger.info("Opened RabbitMQ Admin site")
```
- 'connect_and_setup_queues()'
```bash
def connect_and_setup_queues(host, queue_names):
    """
    Connect to RabbitMQ server, delete existing queues, and declare them anew.

    Parameters:
        host (str): the host name or IP address of the RabbitMQ server
        queue_names (list): list of queue names to delete and declare
    """
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        channel = connection.channel()

        # Delete existing queues and declare them anew
        for queue_name in queue_names:
            channel.queue_delete(queue=queue_name)
            channel.queue_declare(queue=queue_name, durable=True)

        return connection, channel
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Connection to RabbitMQ server failed: {e}")
        sys.exit(1)
```
- 'send_message()'
```bash
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
```
- 'process_csv_and_send_messages()'
```bash
def process_csv_and_send_messages(filename, channel, queue_names, delay):
    """
    Read tasks from a CSV file and send messages to the appropriate queues.

    Parameters:
        filename (str): the name of the CSV file to read from
        channel: the communication channel to the RabbitMQ server
        queue_names (list): list of queue names to send messages to
        delay (int): delay in seconds between sending messages
    """
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
                    send_message(channel, queue_names[0], f"{timestamp}, {smoker_temp}")
                if food_a_temp_str:
                    food_a_temp = float(food_a_temp_str)
                    send_message(channel, queue_names[1], f"{timestamp}, {food_a_temp}")
                if food_b_temp_str:
                    food_b_temp = float(food_b_temp_str)
                    send_message(channel, queue_names[2], f"{timestamp}, {food_b_temp}")

                time.sleep(delay)  # Simulate sleep between messages 30 seconds
    except FileNotFoundError:
        logger.error(f"CSV file {filename} not found.")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Error processing CSV: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)
```
- 'main'
```bash
def main(host, queue_names, filename, delay):
    """
    Main function to set up queues and process the CSV file.

    Parameters:
        host (str): the host name or IP address of the RabbitMQ server
        queue_names (list): list of queue names to delete and declare
        filename (str): the name of the CSV file to read from
        delay (int): delay in seconds between sending messages
    """
    # Get connection and channel
    connection, channel = connect_and_setup_queues(host, queue_names)

    try:
        # Process CSV and send messages
        process_csv_and_send_messages(filename, channel, queue_names, delay)
    finally:
        # Close the connection to the server
        if connection.is_open:
            connection.close()
```
5. Finally, call the main function, which completes the following:
- Establishes a connection to the RabbitMQ server running on localhost.
- Deletes any existing queues named "01-smoker", "02-food-A", and "03-food-B" and then declares new queues with these names.
- Processes a CSV file containing smoker temperature data.
- For each row in the CSV file, it extracts the timestamp, smoker temperature, food A temperature, and food B temperature.
- If the smoker temperature is available (not empty), it converts it to a float and sends a message to the "01-smoker" queue.
- Similarly, if food A or food B temperatures are available, it converts them to float and sends messages to the respective queues.

```bash
if __name__ == "__main__":
    offer_rabbitmq_admin_site()
    main(HOST, QUEUE_NAMES, CSV_FILE, DELAY)
```

## Screenshots

See a running example of the code executing in the terminal, as well as an example of RabbitMQ Admin displaying that all queues are running:
![RabbitMQ Admin](images\AdminQueues.png)
![Terminal Initial Execution](images\InitialExecute.png)
![Terminal Sending Data to Queue](images\SendingData.png)

## Future Enhancements
- Consumers: Next module will see the addition of consumers to process the messages from the queues. 
- Alerts: Implementing alter mechanisms for events detected in temperature data (via email, etc.).







