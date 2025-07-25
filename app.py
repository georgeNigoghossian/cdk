#!/usr/bin/env python3

import aws_cdk as cdk

from cdk_datacamp.cdk_datacamp_stack import CdkDatacampStack


app = cdk.App()
CdkDatacampStack(app, "CdkDatacampStack")

app.synth()
