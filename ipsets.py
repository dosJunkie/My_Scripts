import http.client
import subprocess
import ipaddress
import socket
import boto3
import math
import ssl
import sys
import re


def eprint(*args, **kwargs):
    """
    Print to stderr
    """
    print(*args, file=sys.stderr, **kwargs)


class BlocklistsIpset:
    """
    Implements a downloader and updater for IPset using urls and subdomain passed in argvs.
    Supports IPv4 and IPv6.
    """

    def __init__(self, fqdns, block_list_subdomains):
        self.client = boto3.client('wafv2')
        self.Project_Name = "i14"
        self.API_CALL_NUM_RETRIES = 3
        self.block_list_fqdns = fqdns
        self.block_list_subs = block_list_subdomains

        self.blocklist_list = list()

        self.private_v6 = [
            "ff00::/8",
            "fe80::/10",
            "fd00::/8"
        ]

        self.private_v4 = [
            "0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "172.16.0.0/12",
            "192.168.0.0/16", "169.254.0.0/16", "255.0.0.0/8",
            "224.0.0.0/4"
        ]

        self.public_CIDR_v4 = "^(\d+)(?!10)\.(\d+)(?<!192\.168)(?<!172\.(1[6-9]|2\d|3[0-1]))\.(\d+)\.(\d+)\/\d\d"

        self.public_v4 = "^(\d+)(?!10)\.(\d+)(?<!192\.168)(?<!172\.(1[6-9]|2\d|3[0-1]))\.(\d+)\.(\d+)$"

    def get_set(self, Name, Id):
        response = self.client.get_ip_set(
            Name=name,
            Scope='CLOUDFRONT',
            Id=Id
        )
        return response

    def get_web_acl(self, Name, Id, Scope):
        response = self.client.get_web_acl(
            Name=Name,
            Scope=Scope,
            Id=Id
        )
        return response

    def get_rule_group(self, Name, Id, Scope):
        response = self.client.get_rule_group(
            Name=Name,
            Scope=Scope,
            Id=Id
        )
        return response

    def get_ips(self):
        """
        Download the blocklist using HTTPS and TLSv1.2 or higher.
        """
        ctx = ssl.create_default_context()
        ctx.options |= ssl.OP_NO_TLSv1
        ctx.options |= ssl.OP_NO_TLSv1_1
        ctx.options |= ssl.OP_NO_COMPRESSION

        # initiate a secure HTTPS connection to get the list
        iterb = 0

        for url in self.block_list_fqdns:

            connection = http.client.HTTPSConnection(
                url,
                context=ctx, timeout=5)
            try:
                connection.connect()
            except:
                eprint("Error while connecting.")

            try:
                connection.request("GET", self.block_list_subs[iterb])
                iterb += 1
            except socket.error as e:
                eprint("Socket error: {}".format(e))
                return False
            except socket.timeout as timeout:
                eprint("Socket error: Connection timed out.")
                return False

            response = connection.getresponse()

            if response.status != 200:
                eprint("Server responded with statuscode {}. Aborting".format(
                    response.status))
                return False

            body = response.read()
            if not body:
                eprint("Server didn't send us any data.")
                return False

            block_list = body.decode().split("\n")
            ips = self.process_blocklist(block_list)
            self.blocklist_list = ips + self.blocklist_list
        return self.blocklist_list

    def process_blocklist(self, ips):
        """
        Filter the downloaded blacklist for bogons, private, multicast, and duplicate addresses.
        """
        ipset = set()

        for ip in ips:
            test = re.search(self.public_v4, ip)
            CIDR_test = re.search(self.public_CIDR_v4, ip)
            if CIDR_test:
                ipset.add(CIDR_test.group())
            elif test:
                match = test.group()
                match = match + "/32"
                ipset.add(match)
        ipset = list(ipset)
        return ipset

    def waf_create_set(self, name, scope, ip_ver, ip_list, desc):

        iterb = 0
        start = 0
        end = 10000
        all_responses = {}

        if len(ip_list) < 10000:
            count = 1
        else:
            count = len(ip_list) / 10000
            if count > int(count):
                count = int(count) + 1

        for _ in range(count):
            proper_name = self.block_list_fqdns[iterb].replace(".", "_")
            iterb += 1
            response = self.client.create_ip_set(
                Name=proper_name,
                Scope=scope,
                Description=desc,
                IPAddressVersion=ip_ver,
                Addresses=ip_list[start:end]
            )
            start = end
            end += 10000
            all_responses[proper_name] = response

        return all_responses

    # def waf_update_set(self, ip_set_id, ip_list, action, ip_ver, ):
    #     response_list = []
    #     if ip_list != []:
    #     else:
    #         return "This list is empty."
    #     for ip in ip_list:
    #         try:
    #             response = self.client.update_ip_set(IPSetId=ip_set_id,
    #                                                  ChangeToken=self.client.get_change_token()[
    #                                                      'ChangeToken'],
    #                                                  Updates=[
    #                                                      {
    #                                                          'Action': action,
    #                                                          'IPSetDescriptor': {
    #                                                              'Type': ip_ver,
    #                                                              'Value': ip
    #                                                          }
    #                                                      },
    #                                                  ]
    #                                                  )
    #             response_list.append(response)
    #         except Exception as e:
    #             delay = 2
    #             print("[waf_update_ip_set] Retrying in %d seconds..." % (delay))
    #             time.sleep(delay)
    #         else:
    #             print("[waf_update_ip_set] Failed ALL attempts to call API")

    #     return response_list

    def create_web_acl(self, Scope, Default_Action, Desc):
        response = self.client.create_web_acl(
            Name=self.Project_Name,
            Scope=Scope,
            DefaultAction={Default_Action: {
                "CustomRequestHandling": {
                    "InsertHeaders": [
                        {
                            "Name": self.Project_Name,
                            "Value": self.Project_Name
                        }
                    ]
                }
            }, },
            VisibilityConfig={
                "CloudWatchMetricsEnabled": False,
                "MetricName": self.Project_Name,
                "SampledRequestsEnabled": False
            },
            Description=Desc)

        return response

    def apply_web_acl(self, acl_arn, resource_arn):
        response = self.client.associate_web_acl(
            WebACLArn=acl_arn,
            ResourceArn=resource_arn
        )
        return response

    def update_web_acl(self, ID, Scope, Default_Action):
        response = self.client.update_web_acl(
            Name=self.Project_Name,
            Scope=Scope,
            DefaultAction={Default_Action: {
                "CustomRequestHandling": {
                    "InsertHeaders": [
                        {
                            "Name": self.Project_Name,
                            "Value": self.Project_Name
                        }
                    ]
                }
            }, },
            Id=ID,
            LockToken='59687c5b-7e8e-47e0-af55-cd851043f78f',
            Rules=[{
                "Name": "i14",
                "Priority": 0,
                "Statement": {
                    "IPSetReferenceStatement": {
                        "ARN": "arn:aws:wafv2:us-east-1:092333050644:global/ipset/feeds_dshield_org/5e81c7b1-e06c-47d7-a9e7-f93f839a5247"
                    }
                },
                "Action": {
                    "Block": {}
                },
                "VisibilityConfig": {
                    "SampledRequestsEnabled": True,
                    "CloudWatchMetricsEnabled": True,
                    "MetricName": "i14"
                }
            }],
            VisibilityConfig={
                "SampledRequestsEnabled": True,
                "CloudWatchMetricsEnabled": True,
                "MetricName": "i14"}
        )

        return response

    def waf_delete_ipset(self, set_list):
        reponse_list = []
        if set_list != []:
            pass
        else:
            return "This list is empty."
        for ip in set_list:
            find = self.client.list_ip_sets(
                # Unknown parameter in input: "Scope", must be one of: NextMarker, Limit
                Scope='CLOUDFRONT',
            )
        Id = ""
        for i in find:
            if i['IPSets']['Name'] == ip:
                Id = i['IPSets']['Id']

        token = self.get_set(name=ip, Id=Id)
        token = token['LockToken']
        response = self.client.delete_ip_set(
            Name=ip,
            Scope='CLOUDFRONT',
            Id=Id,
            LockToken=token
        )
        response_list.append(response)

        return response_list
        return find
