"""
RBAC Collector — Captures role assignments via Microsoft Graph API.
Tracks who has access to what, when it changed.
"""
import json
import os
import sys
from datetime import datetime, timezone

from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient
import requests


def get_graph_token():
    cred = DefaultAzureCredential()
    token = cred.get_token("https://graph.microsoft.com/.default")
    return token.token


def get_cosmos_container():
    client = CosmosClient(
        os.environ["COSMOS_ENDPOINT"],
        credential=os.environ["COSMOS_KEY"]
    )
    db = client.get_database_client("security-snapshots")
    return db.get_container_client("rbac-snapshots")


def snapshot_rbac(subscription_id: str):
    token = get_graph_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    container = get_cosmos_container()
    timestamp = datetime.now(timezone.utc).isoformat()

    # Get role assignments for subscription scope
    url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    assignments = resp.json().get("value", [])

    snapshot = {
        "id": f"rbac__{subscription_id}__{timestamp}",
        "subscriptionId": subscription_id,
        "resourceType": "Microsoft.Authorization/roleAssignments",
        "timestamp": timestamp,
        "assignmentCount": len(assignments),
        "assignments": [
            {
                "roleDefinitionId": a["properties"]["roleDefinitionId"],
                "principalId": a["properties"]["principalId"],
                "principalType": a["properties"].get("principalType", "Unknown"),
                "scope": a["properties"]["scope"],
            }
            for a in assignments
        ],
    }
    container.upsert_item(body=snapshot)
    print(f"[RBAC] Captured {len(assignments)} assignments for {subscription_id}")


if __name__ == "__main__":
    sub_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    if not sub_id:
        print("AZURE_SUBSCRIPTION_ID required")
        sys.exit(1)
    snapshot_rbac(sub_id)
