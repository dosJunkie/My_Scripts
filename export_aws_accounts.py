import boto3


client = boto3.client("organizations")


def get_accounts():
accounts = []
params = {
"MaxResults": 20,
}
paginator = client.get_paginator("list_accounts")

for page in paginator.paginate(**params):
accounts.extend(page["Accounts"])

return accounts


def lambda_handler(event, context):
accounts = [{"AccountId": str(account["Id"])} for account in get_accounts()]

return {
"Result": "Success",
"Total": len(accounts),
"Accounts": accounts,
}
