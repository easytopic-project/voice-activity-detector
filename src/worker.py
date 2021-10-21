import pika
import time
import os
import json
import logging
from vad.main import main
from files_ms_client import download, upload

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

FILES_SERVER = os.environ.get("FILES_SERVER", "localhost:3001") 
QUEUE_SERVER_HOST, QUEUE_SERVER_PORT = os.environ.get("QUEUE_SERVER", "localhost:5672").split(":")
Q_IN = os.environ.get("INPUT_QUEUE_NAME", "vad_in")
Q_OUT = os.environ.get("OUTPUT_QUEUE_NAME", "vad_out")

def callback(ch, method, properties, body):
    try:
        print(" [x] Received %r" % body, flush=True)
        args = json.loads(body)
        file = download(args['file']['name'], url="http://" + FILES_SERVER, buffer=True)
        data = main(file)  # calls the VAD algorithm
        try:
            uploaded = upload(data, url="http://" + FILES_SERVER, buffer=True, mime='text/plain')

            # Posts low level features jobs
            message = {
                **args,
                'vad-output': uploaded
                }
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=QUEUE_SERVER_HOST, port=QUEUE_SERVER_PORT))
            channel = connection.channel()

            channel.queue_declare(queue=Q_OUT, durable=True)
            channel.basic_publish(
                exchange='', routing_key=Q_OUT, body=json.dumps(message))
                
        except Exception as e:
            print(e, flush=True)
            LOGGER.info('Error Inserting % ' % e)

    except Exception as e:
        print(e, flush=True)
        logging.info('error')

    print(" [x] Done", flush=True)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def consume():
    logging.info('[x] start consuming')
    success = False
    while not success:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=QUEUE_SERVER_HOST, port=QUEUE_SERVER_PORT))
            channel = connection.channel()
            success = True
        except:
            time.sleep(30)
            pass

    channel.queue_declare(queue=Q_IN, durable=True)
    channel.queue_declare(queue=Q_OUT, durable=True)
    print(' [*] Waiting for messages. To exit press CTRL+C', flush=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=Q_IN, on_message_callback=callback)

    channel.start_consuming()


consume()
