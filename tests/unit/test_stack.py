import aws_cdk as cdk
from aws_cdk.assertions import Template
from cdk.StorageWithLambda import StorageWithLambda

def test_s3_bucket_created():
    app = cdk.App()
    stack = cdk.Stack(app, "TestStack")

    StorageWithLambda(stack, "MyConstruct")

    template = Template.from_stack(stack)
    template.resource_count_is("AWS::S3::Bucket", 1)