import json, requests, boto3, os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

from graphapi import GraphAPI


SNS_CLIENT = boto3.client('sns')
S3_CLIENT = boto3.client('s3')
S3_RES = boto3.resource('s3')

S3_BUCKET_NAME = "instragram-post-scheduler"
APP_PARAM_JSON_NAME = "app_parameters.json"
GRAPHAPI_PARAM_JSON_NAME = "GraphAPI_parameters.json"


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

def send_sns(msg:str, subject:str="💥WARNING: ThisNightSkyDoesNotExist encountered a problem"):
    print(msg)
    SNS_CLIENT.publish(
        TargetArn=os.environ['snsARN'],
        Subject=subject,
        Message=msg
    )


class QueueCSV():
    def __init__(self, csv_queue_path: Path) -> None:
        self.csv_queue_path = csv_queue_path
        self.queue_df = pd.read_csv(csv_queue_path)

    def peek(self):
        if self._is_empty():
            return None
        top_row = self.queue_df[self.queue_df.status == False].iloc[0]
        return dict(photo_url=top_row.photo_url, description=top_row.description)
    
    def pop(self):
        if self._is_empty():
            return None
        top_row_id = self.queue_df[self.queue_df.status == False].iloc[0].name
        top_row = self.queue_df.iloc[top_row_id]
        self.queue_df.at[top_row_id, 'status'] = True
        self.queue_df.to_csv(self.csv_queue_path, index=False)
        return dict(photo_url=top_row.photo_url, description=top_row.description)

    def _is_empty(self):
        return self.queue_df.status.all()

    def __len__(self):
        return int((~self.queue_df.status).sum())

    
def lambda_handler(event, context):

    event_type = event.get("type", "empty")
    if event_type == "empty" and context is not None:
        print("Production trigger...")
    elif event_type == "test":
        print("Testing trigger...")
    else:
        print("Unknown trigger...")

    # Fetch GraphAPI parameters from S3 bucket
    graphapi_params = json.loads(S3_CLIENT.get_object(
        Bucket=S3_BUCKET_NAME,
        Key=GRAPHAPI_PARAM_JSON_NAME,
    )['Body'].read())
    print(json.dumps(graphapi_params, indent=4))

    # # Fetch application parameters from S3 bucket
    # app_params = json.loads(S3_CLIENT.get_object(
    #     Bucket=S3_BUCKET_NAME,
    #     Key=APP_PARAM_JSON_NAME,
    # )['Body'].read())
    # # print(json.dumps(app_params, indent=4))

    # Initilize GraphAPI
    try:
        graph_api = GraphAPI(graphapi_params)
    except Exception as e:
        send_sns(msg="")
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)})
        }

    # Check for expiration date
    remaining_time_token = graph_api.expiration_date - datetime.now()
    if remaining_time_token < timedelta(days=10):
        send_sns(msg=f"`access_token` expires on {graph_api.expiration_date}. Please renew the GraphAPI access token.")

    # Check image availability for the 5 days to come
    # for day_id in range(5):
    #     if not check_url_exists(get_image_url(app_params['data'])):
    #         send_sns(msg=f"The image database will run out of content in {day_id+1} day{'s' if day_id>0 else ''}.")
    #         break
    #     app_params['data']["name_variable"] = data_name_variable_update(app_params['data']["name_variable"])


    # # Build image URL
    # image_url = get_image_url(app_params["data"])
    # # print("image_url:", image_url)

    # # Post image
    # posting_status, request_container_data, request_publication_data = graph_api.post(
    #     image_url=image_url,
    #     caption=app_params["caption"],
    # )
    # if not posting_status:
    #     send_sns(msg=f"Content posting failed.")
    #     return {
    #         'statusCode': 500,
    #         'body': json.dumps({"error": "Content posting failed"})
    #     }

    # # Update image counter in parameter file
    # app_params['data']["name_variable"] = data_name_variable_update(app_params['data']["name_variable"])
    # S3_RES.Object(S3_BUCKET_NAME, APP_PARAM_JSON_NAME).delete()
    # S3_CLIENT.put_object(
    #     Body=json.dumps(app_params),
    #     Bucket=S3_BUCKET_NAME,
    #     Key=APP_PARAM_JSON_NAME,
    # )

    
    logger_body = {
        "GraphAPI parameters": graphapi_params,
        # "Token availability": str(remaining_time_token),
        # "Image published": str(image_url),
        # "GraphAPI response": {
        #     "Request container": request_container_data,
        #     "Request publication": request_publication_data
        # }
    }
    print(logger_body)
    return {
        'statusCode': 200,
        'body': logger_body
    }
