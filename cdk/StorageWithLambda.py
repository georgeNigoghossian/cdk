from constructs import Construct
from aws_cdk import aws_s3 as s3, aws_lambda as lambda_

class StorageWithLambda(Construct):
    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)
        self.bucket = s3.Bucket(self, "MyBucket")

        self.function = lambda_.Function(
            self,
            "MyFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_asset("lambda")
        )
        self.bucket.grant_read_write(self.function)