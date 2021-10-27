import boto3
import pprint
import os
import docker
import base64  
import re

class EcsBotoThree():
    #Its a class but with hardcodes, so moving forward the classes take inputs to fill empty values.
    #Even region depdends on aws configure, so it gets overwritten when executed.
    def __init__(self, name, region, ec2_tag):
        # Credentials & Region
        # Set Secret & Access Key Variables
        #self.access_key = os.environ["AWS_ACCESS_KEY_ID"]
        #self.secret_key = os.environ["AWS_SECRET_ACCESS_KEY"]
        self.region = region
        # ECS Details
        self.cluster_name = name + "_Cluster"
        self.service_name = name + "_Service"
        self.task_name = name
        self.name = name
        self.ec2_tag = ec2_tag
        # Let's use Amazon ECR
        self.ecr_client = boto3.client(
            'ecr',
            #aws_access_key_id=self.access_key,
            #aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        # Let's use Amazon ECS
        self.ecs_client = boto3.client(
            'ecs',
            #aws_access_key_id=self.access_key,
            #aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        # Let's use Amazon EC2
        self.ec2_client = boto3.client(
            'ec2',
            #aws_access_key_id=self.access_key,
            #aws_secret_access_key=self.secret_key,
            region_name=self.region
        )


    def create_ecr(self,):
        response = self.ecr_client.create_repository(
            repositoryName=self.name
        )

        response = pprint.pprint(response)
        return response

    def generateSSHKeys(self,):
    #TODO: Make function

        key_name = self.name # Add timestamp Time
        outfile = open(key_name + '.pem', 'w')
        key_pair = self.ec2_client.create_key_pair(KeyName=key_name, DryRun=False)
        KeyPairOut = str(key_pair.key_material)
        outfile.write(KeyPairOut)
        outfile.close()
        print('Key Pair has been created.')
        os.chmod(key_name + '.pem', 0o400)

    def build_docker_image(self, ):
        """Build Docker image, push to AWS and update ECS service.

        :rtype: None"""

        # build Docker image
        # assumes this file is in same directory as Dockerfile
        docker_client = docker.from_env()
        image, build_log = docker_client.images.build(
            path='.', tag=self.name + ":latest", rm=True)

        # get AWS ECR login token
        ecr_client = boto3.client(
            'ecr', region_name=self.region)

        ecr_credentials = (
            ecr_client
                .get_authorization_token()
            ['authorizationData'][0])

        ecr_username = 'AWS'

        ecr_password = (
            base64.b64decode(ecr_credentials['authorizationToken'])
                .replace(b'AWS:', b'')
                .decode('utf-8'))

        ecr_url = ecr_credentials['proxyEndpoint']

        # get Docker to login/authenticate with ECR
        docker_client.login(
            username=ecr_username, password=ecr_password, registry=ecr_url)

        # tag image for AWS ECR
        ecr_repo_name = '{}/{}'.format(
            ecr_url.replace('https://', ''), self.name + ":latest")

        image.tag(ecr_repo_name, tag='latest')

        # push image to AWS ECR
        push_log = docker_client.images.push(ecr_repo_name, tag="latest")

        return push_log


    def launch_ecs_cluster(self,):
        response = self.ecs_client.create_cluster(
            clusterName=self.cluster_name
        )

        response = pprint.pprint(response)
        return response


    def launch_ec2(self, ami, size, SecGroupId, SubnetId,):

        # Create EC2 instance(s) in the cluster
        # For now I expect a default cluster to be there

        # By default, your container instance launches into your default cluster.
        # If you want to launch into your own cluster instead of the default,
        # choose the Advanced Details list and paste the following script
        # into the User data field, replacing your_cluster_name with the name of your cluster.
        # !/bin/bash
        # echo ECS_CLUSTER=your_cluster_name >> /etc/ecs/ecs.config

        #TODO: Add more tags, disks, nics, everything you can possible want
        response = self.ec2_client.run_instances(
            ImageId=ami, #"ami-07c1207a9d40bc3bd"
            MinCount=1,
            MaxCount=1,
            InstanceType=size, # "t2.small",
            Monitoring={
                            'Enabled': False
                        },
            SecurityGroupIds=[
                                SecGroupId,
                             ],
            # SecurityGroups=[
            #                 'string',
            #                ],
            SubnetId=SubnetId,
            # CpuOptions={
            #                 'CoreCount': 123,
            #                 'ThreadsPerCore': 123
            #             },
            UserData="#!/bin/bash \n echo ECS_CLUSTER=" + self.cluster_name + " >> /etc/ecs/ecs.config",
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': self.ec2_tag
                        },
                    ]
                },            ], 
            # NetworkInterfaces=[
            #     {
            #         'AssociatePublicIpAddress': True|False,
            #         'DeleteOnTermination': True|False,
            #         'Description': 'string',
            #         'DeviceIndex': 123,
            #         'Groups': [
            #             'string',
            #         ],
            #         'Ipv6AddressCount': 123,
            #         'Ipv6Addresses': [
            #             {
            #                 'Ipv6Address': 'string'
            #             },
            #         ],
            #         'NetworkInterfaceId': 'string',
            #         'PrivateIpAddress': 'string',
            #         'PrivateIpAddresses': [
            #             {
            #                 'Primary': True|False,
            #                 'PrivateIpAddress': 'string'
            #             },
            #         ],
            #         'SecondaryPrivateIpAddressCount': 123,
            #         'SubnetId': 'string',
            #         'InterfaceType': 'string'
            #     },
            #                     ],
            # Placement={
            #         'AvailabilityZone': 'string',
            #         'Affinity': 'string',
            #         'GroupName': 'string',
            #         'PartitionNumber': 123,
            #         'HostId': 'string',
            #         'Tenancy': 'default'|'dedicated'|'host',
            #         'SpreadDomain': 'string',
            #         'HostResourceGroupArn': 'string'
            #           },
                   )

        response = pprint.pprint(response)
        return response


    def ecs_task_definition(self, RepoName, cpu, memory, MemorySoftLimit, ContainerPort, HostPort, protocol, essential,):
        # Pull ECR info
        ecr_info = self.ecr_client.describe_repositories(
                                                         repositoryNames=[RepoName]
                                                        )
        # Pulls repository-url /image:tag
        doc_image = ecr_info['repositories'][0]['repositoryUri'] + ":latest"
        # Create a task definition
        #TODO: Gotta yank account info from another call, and feed in down here
        response = self.ecs_client.register_task_definition(
            family=self.name,
            networkMode="bridge",
            containerDefinitions=[
                {
                    "name": self.name,
                    "image": doc_image,
                    "cpu": cpu,
                    "memory": memory,
                    "memoryReservation": MemorySoftLimit,
                    "portMappings": [
                        {
                            "containerPort": ContainerPort,
                            "hostPort": HostPort,
                            "protocol": protocol
                        }
                    ],
                    "essential": essential,
                    "entryPoint": [],
                    "command": [],
                    "environment": [
                        {
                            "name": "BEEF_PASSWORD",
                            "value": "feeb33"
                        },
                        {
                            "name": "BEEF_USER",
                            "value": "beef-admin"
                        }
                    ],
                    "mountPoints": [],
                    "volumesFrom": [],
                    "user": "beef",
                    "workingDirectory": "/home/beef/"
                }
            ]
        )


        response = pprint.pprint(response)
        return response


    def launch_ecs_service(self, count, maximum, minimum):
        """Create service with exactly 1 desired instance of the task
            Info: Amazon ECS allows you to run and maintain a specified number
            (the "desired count") of instances of a task definition
            simultaneously in an ECS cluster."""
        response = self.ecs_client.create_service(
            cluster=self.cluster_name,
            serviceName=self.service_name,
            taskDefinition=self.task_name,
            desiredCount=count,
            deploymentConfiguration={
                'maximumPercent': maximum,
                'minimumHealthyPercent': minimum
            }
        )

        response = pprint.pprint(response)
        return response


        # Shut everything down and delete service/instance/cluster
    def terminate_ecs_sevice(self,):
        try:
            # Set desired service count to 0 (obligatory to delete)
            response = self.ecs_client.update_service(
                cluster=self.cluster_name,
                service=self.service_name,
                desiredCount=0
            )
            # Delete service
            response = self.ecs_client.delete_service(
                cluster=self.cluster_name,
                service=self.service_name
            )
            response = pprint.pprint(response)
        except:
            print("Service not found/not active")
        return response


    def de_register_task_definitions(self,):
        # List all task definitions and revisions
        response = self.ecs_client.list_task_definitions(
            familyPrefix=self.task_name,
            status='ACTIVE'
        )

        # De-Register all task definitions
        for task_definition in response["taskDefinitionArns"]:
            # De-register task definition(s)
            deregister_response = self.ecs_client.deregister_task_definition(
                taskDefinition=task_definition
            )
            deregister_response = pprint.pprint(deregister_response)
            return deregister_response


    def terminate_ec2_instaces(self, ):
        # Terminate virtual machine(s)
        #TODO: Be 100% sure this only deletes what was created.
        # Gathers ec2 instance info & pulls ecs owner ID 
        ec2_instance_info = self.ec2_client.describe_instances()

        # Stores instnce ID's that have applicable tag
        instance_ids = []

        # Checks if instance has a tag and if the image has the applicable tag
        for ec2_instance in ec2_instance_info["Reservations"]:
            if "Tags" in ec2_instance["Instances"][0].keys() and ec2_instance["Instances"][0]["Tags"][0]["Value"] == self.ec2_tag:
                instance_ids.append(ec2_instance["Instances"][0]["InstanceId"])

        # Terminates instances stored in instance_ids
        ec2_termination_resp = self.ec2_client.terminate_instances(
            DryRun=False,
            InstanceIds=instance_ids
        )

        response = pprint.pprint(ec2_termination_resp)
        return response


    def delete_cluster(self,):
        # Finally delete the cluster
        response = self.ecs_client.delete_cluster(
            cluster=self.cluster_name
        )
        response = pprint.pprint(response)
        return response

    def delete_images(self,):
        # Finally delete the cluster
        response = self.ecr_client.batch_delete_image(
            repositoryName=self.name,

    #TODO get list of image ids
            imageIds = [
            {
                'imageDigest': 'string',
                'imageTag': 'string'
            },
            ]
        )
        response = pprint.pprint(response)
        return response

    def delete_ecr(self,):
        # Finally delete the cluster
        response = self.ecr_client.delete_repository(
            repositoryName=self.name
        )
        response = pprint.pprint(response)
        return response



