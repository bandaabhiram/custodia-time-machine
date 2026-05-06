"""
Conditional Access Collector — Snapshots Entra ID CA policies.
Requires Microsoft Graph API permissions: Policy.Read.All
"""
import json
import os
import sys
from datetime import datetime, timezone

from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient
import requests


def get_token():
    cred = DefaultAzureCredential()
    return cred.get_token("https://graph.microsoft.com/.default").token


def get_cosmos_container():
    client = CosmosClient(
        os.environ["COSMOS_ENDPOINT"],
        credential=os.environ["COSMOS_KEY"]
    )
    db = client.get_database_client("security-snapshots")
    return db.get_container_client("config-snapshots")


def snapshot_ca_policies(tenant_id: str):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    container = get_cosmos_container()
    timestamp = datetime.now(timezone.utc).isoformat()

    url = "https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    policies = resp.json().get("value", [])

    for policy in policies:
        snapshot = {
            "id": f"ca__{policy['id']}__{timestamp}",
            "subscriptionId": tenant_id,
            "resourceType": "Microsoft.Graph/conditionalAccessPolicy",
            "resourceId": policy["id"],
            "resourceName": policy["displayName"],
            "timestamp": timestamp,
            "properties": {
                "state": policy.get("state"),
                "conditions": policy.get("conditions", {}),
                "grantControls": policy.get("grantControls", {}),
                "sessionControls": policy.get("sessionControls", {}),
            },
        }
        container.upsert_item(body=snapshot)
        print(f"[CA] Snapshotted {policy['displayName']}")


if __name__ == "__main__":
    tenant = os.environ.get("AZURE_TENANT_ID", "common")
    snapshot_ca_policies(tenant)
