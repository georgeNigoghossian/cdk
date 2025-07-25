# lambda/index.py

def handler(event, context):
    return {
        "statusCode": 200,
        "body": "Hello from CDK Lambda!"
    }
