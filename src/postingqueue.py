import pandas as pd, io
import numpy as np

class PostingQueueS3CSV():
    def __init__(self, s3_client:str, s3_bucket:str, s3_key:str) -> None:

        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key

        self.queue_df = pd.DataFrame()
        self._pull_csv()

    def _pull_csv(self):
        response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=self.s3_key)
        status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")

        if status == 200:
            print(f"Successful S3 get_object response. Status - {status}")
            self.queue_df = pd.read_csv(response.get("Body"))
        else:
            print(f"Unsuccessful S3 get_object response. Status - {status}")
        return status

    def _push_csv(self):
        with io.StringIO() as csv_buffer:
            self.queue_df.to_csv(csv_buffer, index=False)

            response = self.s3_client.put_object(
                Bucket=self.s3_bucket, Key=self.s3_key, Body=csv_buffer.getvalue()
            )

            status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")

            if status == 200:
                print(f"Successful S3 put_object response. Status - {status}")
            else:
                print(f"Unsuccessful S3 put_object response. Status - {status}")
        return status

    def peek(self):
        if self._is_empty():
            return None
        top_row = self.queue_df[self.queue_df.status == False].iloc[0]
        return dict(image_url=top_row.image_url, caption=top_row.caption if not pd.isnull(top_row.caption) else "")
    
    def pop(self):
        if self._is_empty():
            return None
        top_row_id = self.queue_df[self.queue_df.status == False].iloc[0].name
        top_row = self.queue_df.iloc[top_row_id]
        self.queue_df.at[top_row_id, 'status'] = True
        self._push_csv()
        return dict(image_url=top_row.image_url, caption=top_row.caption if not pd.isnull(top_row.caption) else "")

    def _is_empty(self):
        return self.queue_df.status.all()

    def __len__(self):
        return int((~self.queue_df.status).sum())
