from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_elasticloadbalancingv2 as elbv2,
    aws_autoscaling as autoscaling,
    aws_elasticache as elasticache,
    Duration,
    CfnOutput, RemovalPolicy
)
from constructs import Construct


class WebApplicationStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = ec2.Vpc(self, "AppVpc",
                           max_azs=3,
                           subnet_configuration=[
                               ec2.SubnetConfiguration(
                                   name="Public",
                                   subnet_type=ec2.SubnetType.PUBLIC,
                                   cidr_mask=24
                               ),
                               ec2.SubnetConfiguration(
                                   name="Private",
                                   subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                                   cidr_mask=24
                               )
                           ],
                           nat_gateways=1
                           )

        self.alb_sg = ec2.SecurityGroup(self, "ALBSecurityGroup",
                                        vpc=self.vpc,
                                        description="Allow HTTP access to ALB",
                                        allow_all_outbound=True
                                        )
        self.alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP from anywhere")

        self.alb = elbv2.ApplicationLoadBalancer(self, "ALB",
                                                 vpc=self.vpc,
                                                 internet_facing=True,
                                                 security_group=self.alb_sg
                                                 )
        self.http_listener = self.alb.add_listener("HttpListener", port=80, open=True)

        self.web_sg = ec2.SecurityGroup(self, "WebSecurityGroup",
                                        vpc=self.vpc,
                                        description="Allow HTTP/SSH from ALB and within VPC",
                                        allow_all_outbound=True
                                        )
        self.web_sg.add_ingress_rule(self.alb_sg, ec2.Port.tcp(80), "Allow HTTP from ALB")
        self.web_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow SSH from anywhere (for demo)")

        ami = ec2.MachineImage.latest_amazon_linux2(
            edition=ec2.AmazonLinuxEdition.STANDARD,
            cpu_type=ec2.AmazonLinuxCpuType.X86_64
        )

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "yum update -y",
            "yum install -y nginx",
            "systemctl start nginx",
            "systemctl enable nginx",
            f'echo "Hello from $(hostname -f)!" > /usr/share/nginx/html/index.html'
        )

        self.asg = autoscaling.AutoScalingGroup(self, "ASG",
                                                vpc=self.vpc,
                                                instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3,
                                                                                  ec2.InstanceSize.MICRO),
                                                machine_image=ami,
                                                vpc_subnets=ec2.SubnetSelection(
                                                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                                                min_capacity=1,
                                                max_capacity=3,
                                                security_group=self.web_sg,
                                                user_data=user_data
                                                )

        self.http_listener.add_targets("ASGTarget", port=80, targets=[self.asg])

        self.rds_sg = ec2.SecurityGroup(self, "RDSSecurityGroup",
                                        vpc=self.vpc,
                                        description="Allow DB access from Web Servers",
                                        allow_all_outbound=True
                                        )
        self.rds_sg.add_ingress_rule(self.web_sg, ec2.Port.tcp(3306), "Allow MySQL from Web Servers")

        self.db_instance = rds.DatabaseInstance(self, "MyDatabase",
                                                engine=rds.DatabaseInstanceEngine.mysql(
                                                    version=rds.MysqlEngineVersion.VER_8_0_34),
                                                instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3,
                                                                                  ec2.InstanceSize.MICRO),
                                                vpc=self.vpc,
                                                vpc_subnets=ec2.SubnetSelection(
                                                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                                                security_groups=[self.rds_sg],
                                                multi_az=False,
                                                allocated_storage=20,
                                                backup_retention=Duration.days(0),
                                                removal_policy=RemovalPolicy.DESTROY,
                                                publicly_accessible=False,
                                                database_name="mydb"
                                                )

        CfnOutput(self, "RDS_Endpoint", value=self.db_instance.db_instance_endpoint_address)
        CfnOutput(self, "RDS_Port", value=self.db_instance.db_instance_endpoint_port)
        CfnOutput(self, "RDS_SecretName",
                  value=self.db_instance.secret.secret_name if self.db_instance.secret else "NoSecretGenerated")

        self.elasticache_sg = ec2.SecurityGroup(self, "ElastiCacheSecurityGroup",
                                                vpc=self.vpc,
                                                description="Allow ElastiCache access from Web Servers",
                                                allow_all_outbound=True
                                                )
        self.elasticache_sg.add_ingress_rule(self.web_sg, ec2.Port.tcp(6379), "Allow Redis from Web Servers")

        self.cache_subnet_group = elasticache.CfnSubnetGroup(self, "CacheSubnetGroup",
                                                             description="Subnet group for ElastiCache",
                                                             subnet_ids=self.vpc.select_subnets(
                                                                 subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids
                                                             )

        self.cache_cluster = elasticache.CfnCacheCluster(self, "MyCacheCluster",
                                                         cache_node_type="cache.t3.micro",
                                                         num_cache_nodes=1,
                                                         engine="redis",
                                                         cache_subnet_group_name=self.cache_subnet_group.ref,
                                                         vpc_security_group_ids=[self.elasticache_sg.security_group_id]
                                                         )
        self.cache_cluster.add_dependency(self.cache_subnet_group)

        CfnOutput(self, "ElastiCache_Endpoint", value=self.cache_cluster.attr_redis_endpoint_address)
        CfnOutput(self, "ElastiCache_Port", value=self.cache_cluster.attr_redis_endpoint_port)

        CfnOutput(self, "ALBDnsName", value=self.alb.load_balancer_dns_name)