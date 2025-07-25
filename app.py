from aws_cdk import App

from cdk.cdk_stack import MyStack

app = App()

MyStack(app, "MyFirstStack")

app.synth()