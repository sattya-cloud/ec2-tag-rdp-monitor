import boto3
import os

ec2_client = boto3.client('ec2')
sns_client = boto3.client('sns')

# Environment variables
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

# Check if required tags are present
def check_tags(instance):
    required_tags = {'Business Unit', 'ITSO Email'}
    tags = instance.get('Tags', [])
    instance_tags = {tag['Key'] for tag in tags}
    missing_tags = required_tags - instance_tags

    return missing_tags
# Check if RDP is open to the internet
def check_rdp_security(instance_id):
    # Describe the security groups attached to the instance
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    security_groups = response['Reservations'][0]['Instances'][0].get('SecurityGroups', [])

    for sg in security_groups:
        sg_id = sg['GroupId']
        # Get the security group details
        sg_response = ec2_client.describe_security_groups(GroupIds=[sg_id])
        for permission in sg_response['SecurityGroups']:
            for ip_permission in permission.get('IpPermissions', []):
                if ip_permission.get('FromPort') == 3389 and '0.0.0.0/0' in [ip['CidrIp'] for ip in ip_permission.get('IpRanges', [])]:
                    return True

    return False

# Send notification to ITSO

def send_warning_email(its_email, message):
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logger.info(f"Using SNS Topic ARN: {SNS_TOPIC_ARN}")

    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="AWS EC2 Warning Notification",
        Message=f"Hello ITSO,\n\n{message}\n\nThanks,\nAWS Monitoring Team"
    )


# Lambda handler
def lambda_handler(event, context):
    response = ec2_client.describe_instances()

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_state = instance['State']['Name']

            # Check for required tags
            missing_tags = check_tags(instance)
            if missing_tags:
                its_email = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'ITSO Email'), 'N/A')
                send_warning_email(
                    its_email,
                    f"Instance {instance_id} is missing required tags: {', '.join(missing_tags)}."
                )

            # Check for RDP open to the internet
            if check_rdp_security(instance_id):
                its_email = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'ITSO Email'), 'N/A')
                send_warning_email(
                    its_email,
                    f"Instance {instance_id} has RDP port (3389) open to the internet (0.0.0.0/0). Please review security settings."
                )

            # Check if production instance is stopped
            if instance_state == 'stopped' and any(tag['Value'] == 'production' for tag in instance.get('Tags', [])):
                its_email = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'ITSO Email'), 'N/A')
                send_warning_email(
                    its_email,
                    f"Production instance {instance_id} has been stopped. Immediate action is required."
                )
