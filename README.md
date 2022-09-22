# Instagram Post Scheduler

This repository includes all the source code and detailed steps to setup an AWS application using Meta's GraphAPI automatically publishing new post on Instagram on a regular basis.

## Setup

### Generate a GraphAPI access token

For a detailed tutorial, follow [this article](https://levelup.gitconnected.com/automating-instagram-posts-with-python-and-instagram-graph-api-374f084b9f2b).

1. Convert your Instagram profile to a Business account: 
    
    [***Instagram Help Center:*** *Set Up a Business Account*](https://help.instagram.com/2358103564437429/?helpref=uf_share)

    **Note:** Instagram Creator accounts are not supported for content publishing.

2. Add a Facebook Page to your Instagram Business account:
        
    [***Instagram Help Center:*** *How to Add or Change the Facebook Page Connected to Your Instagram Business Account*](https://help.instagram.com/399237934150902/?helpref=uf_share)

3. Create a Facebook Developer account that can perform tasks on that page.

    [***Meta for Developers's Doc:*** *Register as a Facebook Developer*](https://developers.facebook.com/docs/development/register/)

4. Generate an access Token through the Graph API explorer, and find your Instagram User ID. You will need the following permissions: `instagram_basic`, `instagram_content_publish`, `public_profile`.

    [***Meta for Developers, Graph API's documentation:*** *Getting Started (1 to 5)*](https://developers.facebook.com/docs/instagram-api/getting-started/)

5. Exchange the short-lived token generate above for a long-lived acces token.

    [***Meta for Developers, Graph API's documentation:*** *Long-Lived Access Tokens*](https://developers.facebook.com/docs/instagram-basic-display-api/guides/long-lived-access-tokens/)

6. Complete [./graphapi_parameters.json](./graphapi_parameters.json) with your long-lived access token (`access_token`) and Instagram User ID (`instagram_account_id`) from from step 4, and your Instagram App key pair (`client_id` and `client_secret`) from your [Meta's developer dashboard](https://developers.facebook.com/) (App Dashboard > Products > Instagram > Basic Display).


### Create application and media S3 buckets


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

### [Optional] Setup SNS notifier

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


### Create Lambda function

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
- Increase memory to 256mb
- Setup Cron job: 0 18 */2 * ? *


## Notes

Images shoulds be less than 8mb