import json
import boto3
from os import environ
from urllib.parse import unquote
from datetime import datetime

from hec import Splunk

client = boto3.client("iam")
hec = Splunk(
url=environ["SPLUNK_URL"],
token=environ["SPLUNK_TOKEN"],
host=environ["SPLUNK_HOST"],
source=environ["SPLUNK_SOURCE"],
source_type=environ["SPLUNK_SOURCETYPE"],
)


def get_policy_doc(PolicyArn, VersionId) -> dict:
policy_doc = client.get_policy_version(PolicyArn=PolicyArn, VersionId=VersionId)
return policy_doc


def get_aws_managed_policies() -> dict:
response = client.list_policies(
Scope="AWS",
OnlyAttached=False,
MaxItems=1000,
)
payloads = []
for item in response["Policies"]:
latest_policy_version = get_policy_doc(item["Arn"], item["DefaultVersionId"])[
"PolicyVersion"
]
latest_policy_version["Document"] = json.loads(
unquote(json.dumps(latest_policy_version["Document"]))
)
item.update(latest_policy_version)

item["CreateDate"] = str(item["CreateDate"])
create_date = datetime.strptime(item["CreateDate"], "%Y-%m-%d %H:%M:%S%z")
item["CreateDate"] = create_date.strftime("%Y-%m-%dT%H:%M:%SZ")

item["UpdateDate"] = str(item["UpdateDate"])
update_date = datetime.strptime(item["UpdateDate"], "%Y-%m-%d %H:%M:%S%z")
item["UpdateDate"] = update_date.strftime("%Y-%m-%dT%H:%M:%SZ")

item.pop("AttachmentCount")
item.pop("PermissionsBoundaryUsageCount")

item = json.loads(json.dumps(item).replace("*", "_asterisk_"))
item = {f"{key[0].lower()}{key[1:]}": value for key, value in item.items()}

payloads.append(item)

len_payloads = len(payloads)
workers_count = round(len_payloads / 15)
if workers_count < 5:
workers_count = 5
elif workers_count > 30:
workers_count = 30

hec.host = "aws"
hec.bulk_send(payloads=payloads, source="AWS::IAM::Policy", workers=workers_count)
print(f"Ended collecting AWS managed policies using {workers_count} workers. Total collected: {len_payloads}")
return {"Account": "aws", "ResourceType": "AWS::IAM::Policy", "Total": len_payloads}


def lambda_handler(event, context) -> dict:
return {
"Success": True,
"Description": f"Collection of AWS managed policies done",
"Result": get_aws_managed_policies(),
}
