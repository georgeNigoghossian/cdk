from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from cdk.StorageWithLambda import StorageWithLambda


class MyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        storage = StorageWithLambda(self, "ReusableComponent")