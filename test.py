#!/usr/bin/python
# TODO:   File "test.py", line 56, in generate_srv_record
#         name_record = name + '.srv.' + domain_name
#         TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'


import boto3, configparser

client = boto3.client('ecs')

config = configparser.ConfigParser()
config.read("./config.ini")
cluster_name = config["default"]['cluster_name']
domain_name = config["default"]['domain_name']

def get_tasks_for_cluster(cluster_name):
    tasks = []
    for task in client.list_tasks(cluster=cluster_name)['taskArns']:
        tasks.append(task)
    return tasks

def get_host_port_from_task(cluster_name, task):
    task_info = client.describe_tasks(cluster=cluster_name,tasks=[task])
    containers = task_info['tasks'][0]['containers']
    for container in containers:
        if container['networkBindings']:
            return container['networkBindings'][0]['hostPort']
        else:
            pass

def get_container_instance_from_task(cluster_name, task):
    task_info = client.describe_tasks(cluster=cluster_name,tasks=[task])
    return task_info['tasks'][0]['containerInstanceArn']

def get_instance_id_from_container_instance(cluster_name, container_instance):
    container_instance = str(container_instance).replace('arn:aws:ecs:us-east-1:464631411360:container/','')
    response = client.describe_container_instances(
        cluster=cluster_name,
        containerInstances=[container_instance])
    return response['containerInstances'][0]['ec2InstanceId']

def get_instance_ip_from_instance_id(instance_id):
    ec2 = boto3.client('ec2')
    instance_info = ec2.describe_instances(InstanceIds=[instance_id])
    return instance_info['Reservations'][0]['Instances'][0]['PrivateIpAddress']

def get_task_name(cluster_name, task):
    task_info = client.describe_tasks(cluster=cluster_name,tasks=[task])
    containers = task_info['tasks'][0]['containers']
    for container in containers:
        if container['networkBindings']:
            return container['name']

def get_hosted_zone_domain(domain_name):
    client = boto3.client('route53', region_name='us-east-1')
    return client.list_hosted_zones_by_name(DNSName=domain_name)['HostedZones'][0]['Id']

def generate_srv_record(host_ip, host_port, name, domain_name):
    client = boto3.client('route53', region_name='us-east-1')
    resourceRecordValue = str('1 10 %s %s' % (host_port, host_ip))
    hosted_zone = get_hosted_zone_domain(domain_name)
    name_record = name + '.srv.' + domain_name
    response = client.change_resource_record_sets(
        HostedZoneId=hosted_zone,
        ChangeBatch={
            'Comment': 'Route53ECS entry',
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': name_record,
                        'Type': 'SRV',
                        'TTL': 60,
                        'ResourceRecords': [
                            {
                                'Value': resourceRecordValue
                            },
                        ],
                    }
                },
            ]
        }
    )
    return response

tasks = get_tasks_for_cluster(cluster_name)

srv_info = {}

for task in tasks:
    srv_info[task] = {}
    srv_info[task]['hostPort'] = get_host_port_from_task(cluster_name, task)
    srv_info[task]['containerInstance'] = get_container_instance_from_task(cluster_name, task)
    srv_info[task]['instanceId'] = get_instance_id_from_container_instance(cluster_name, srv_info[task]['containerInstance'])
    srv_info[task]['ipAddress'] = get_instance_ip_from_instance_id(srv_info[task]['instanceId'])
    srv_info[task]['name']  = get_task_name(cluster_name, task)
    generate_srv_record(srv_info[task]['ipAddress'], srv_info[task]['hostPort'], srv_info[task]['name'], domain_name)
