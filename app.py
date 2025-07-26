from aws_cdk import App
from cdk.WebAppStack import WebApplicationStack # Correct import path

app = App()

WebApplicationStack(app, "MyEnterpriseWebApp")

app.synth()