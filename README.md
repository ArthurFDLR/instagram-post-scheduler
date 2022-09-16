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