import json, requests, boto3, traceback
from datetime import datetime, timedelta
# from pathlib import Path
# import pandas as pd

from graphapi import GraphAPI
from postingqueue import PostingQueueS3CSV

SNS_CLIENT = boto3.client('sns')
S3_CLIENT = boto3.client('s3')
S3_RES = boto3.resource('s3')

APP_BUCKET = "instagram-post-scheduler"
POSTING_QUEUE_KEY = "instagram_post_schedule.csv"
GRAPHAPI_PARAMS_KEY = "graphapi_parameters.json"

SNS_TOPIC_ARN = None # SNS Topic ARN (e.g. "arn:aws:sns:us-east-1:237694347:instagram-post-scheduler-sns")

def check_url_exists(url: str):
    """
    Checks if a url exists
    :param url: url to check
    :return: True if the url exists, false otherwise.
    """
    return requests.head(url, allow_redirects=True).status_code // 100 == 2

def data_name_variable_update(data):
    return data+1

def get_image_url(params_data):
    image_url = f"https://{str(params_data['bucket'])}.s3.amazonaws.com/"
    for folder in params_data["path"]:
        image_url += folder + "/"
    image_url += params_data["name_format"].replace("%name_variable%", str(params_data["name_variable"]))
    return image_url

def send_sns(msg:str, subject:str="Your Instagram Post Scheduler encountered a problem 💥"):
    print(msg)
    try:
        if SNS_ARN is not None:
            SNS_CLIENT.publish(
                TargetArn=SNS_ARN,
                Subject=subject,
                Message=msg
            )
        else:
            print("SNS_ARN hasn't been set.")
    except Exception as e:
        print(f"WARNING: send_sns failed: {e}")


def post_queue_top(graph_api: GraphAPI, queue: PostingQueueS3CSV):

    posting_data = queue.peek()

    posting_status, request_container_data, request_publication_data = graph_api.post(
        image_url=posting_data["image_url"],
        caption=posting_data["caption"],
    )
    if posting_status:
        queue.pop()
    return posting_status, posting_data, request_container_data, request_publication_data
    

def lambda_handler(event, context):

    status_code = 200

    event_type = event.get("type", "empty")
    if event_type == "empty" and context is not None:
        print("Production trigger...")
    elif event_type == "test":
        print("Testing trigger...")
    else:
        print("Unknown trigger...")

    # Fetch GraphAPI parameters from S3 bucket
    graphapi_params = json.loads(S3_CLIENT.get_object(
        Bucket=APP_BUCKET,
        Key=GRAPHAPI_PARAMS_KEY,
    )['Body'].read())
    print(json.dumps(graphapi_params, indent=4))

    # Initilize GraphAPI
    try:
        graph_api = GraphAPI(graphapi_params)
    except Exception as e:
        send_sns(msg=f"GraphAPI initialization failed:\n{traceback.format_exc()}")
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)})
        }

    # Check for expiration date
    print(f"Token expiration date: {graph_api.expiration_date}")
    remaining_time_token = graph_api.expiration_date - datetime.now()
    if remaining_time_token < timedelta(days=10):
        send_sns(msg=f"`access_token` expires on {graph_api.expiration_date}. Please renew the GraphAPI access token.")

    # Initialize posting queue
    posting_queue = PostingQueueS3CSV(
        s3_client=S3_CLIENT,
        s3_bucket=APP_BUCKET,
        s3_key=POSTING_QUEUE_KEY,
    )

    # Check image availability for the week to come
    if len(posting_queue) <= 7:
        send_sns(msg=f"The image database will run out of content in {len(posting_queue)+1} day{'s' if len(posting_queue)>0 else ''}.")

    # Publish new post
    if event_type == "empty" and context is not None:
        posting_status, posting_data, request_container_data, request_publication_data = post_queue_top(graph_api, posting_queue)
        if not posting_status:
            send_sns(msg=f"Content posting failed.")
            status_code = 500
    else:
        posting_data, request_container_data, request_publication_data = posting_queue.peek(), None, None
        print(f"Called in test mode; not publishing image:\n{posting_data}")
    
    logger_body = {
        "Token availability": str(remaining_time_token),
        "Post data": posting_data,
        "GraphAPI response": {
            "Request container": request_container_data,
            "Request publication": request_publication_data
        }
    }

    print(logger_body)
    return {
        'statusCode': status_code,
        'body': logger_body
    }
