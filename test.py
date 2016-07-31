import boto3
from subprocess import call

client = boto3.client('ecs')

cluster_name = '###############
hosted_zone = '###############'

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

def generate_srv_record(host_ip, host_port, name, hosted_zone):
    return call("/usr/bin/cli53" + " rrcreate --replace %s '%s 60 SRV 1 10 %s %s.'" % (hosted_zone, name, host_port, host_ip), shell=True)

tasks = get_tasks_for_cluster(cluster_name)

srv_info = {}

for task in tasks:
    srv_info[task] = {}
    srv_info[task]['hostPort'] = get_host_port_from_task(cluster_name, task)
    srv_info[task]['containerInstance'] = get_container_instance_from_task(cluster_name, task)
    srv_info[task]['instanceId'] = get_instance_id_from_container_instance(cluster_name, srv_info[task]['containerInstance'])
    srv_info[task]['ipAddress'] = get_instance_ip_from_instance_id(srv_info[task]['instanceId'])
    srv_info[task]['name']  = get_task_name(cluster_name, task)
    generate_srv_record(srv_info[task]['ipAddress'], srv_info[task]['hostPort'], srv_info[task]['name'], hosted_zone)
