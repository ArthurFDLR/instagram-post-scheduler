# Instagram Post Scheduler

## Setup

- Create private S3 Bucket 
- Create public S3 Bucket
  - Allow publicj during creation;
  - Add permision:
    ```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPublicRead",
            "Effect": "Allow",
            "Principal": {
                "AWS": "*"
            },
            "Action": "s3:GetObject",
            "Resource": [
                "arn:aws:s3:::instagram-post-scheduler-public/*",
                "arn:aws:s3:::instagram-post-scheduler-public"
            ]
        }
    ]
}
    ```
- create Lambda function with Python runtime
- add S3 permissions:
    Configuration > Permissions > Role Name > Add permissions > Attach policy > Select AmazonS3FullAccess > Attach Policies
- Create test case (Ctrl+Shift+C) with event JSON
    ```
    {
        "type": "test"
    }
    ```
- Package the application i.e. run ./packaging.sh.
- Upload into Lambda function (see ./dist/): Code > Upload from > .zip file
  
- Create SNS Topic (Type: Standard, Name: instagram-post-scheduler-sns, Display Name: Instagram Post Scheduler)
- Create SNS Subscription (Topic ARN: from last step, protocol: Email); Confirm subscription in your emails inbox
- Add policy to Lambda function to publish on SNS Topic (Name: instagram-post-scheduler-sns-publish):
  ```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sns:Publish",
            "Resource": "arn:aws:sns:us-east-1:062411248643:instagram-post-scheduler-sns"
        }
    ]
}
  ```
- Update SNS_ARN in script (see ./lambda_function)