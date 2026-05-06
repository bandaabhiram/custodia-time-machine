"""
NSG Collector — Captures full Network Security Group rule state every 15 minutes.
Stores flattened snapshots in Cosmos DB for forensic timeline queries.
"""
import json
import os
import sys
from datetime import datetime, timezone

from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
from azure.cosmos import CosmosClient


def get_cosmos_container():
    client = CosmosClient(
        os.environ["COSMOS_ENDPOINT"],
        credential=os.environ["COSMOS_KEY"]
    )
    db = client.get_database_client("security-snapshots")
    return db.get_container_client("config-snapshots")


def snapshot_nsg(subscription_id: str):
    credential = DefaultAzureCredential()
    network_client = NetworkManagementClient(credential, subscription_id)
    container = get_cosmos_container()

    timestamp = datetime.now(timezone.utc).isoformat()

    for nsg in network_client.network_security_groups.list_all():
        snapshot = {
            "id": f"{nsg.id}__{timestamp}",
            "subscriptionId": subscription_id,
            "resourceType": "Microsoft.Network/networkSecurityGroups",
            "resourceId": nsg.id,
            "resourceName": nsg.name,
            "resourceGroup": nsg.id.split("/")[4],
            "location": nsg.location,
            "timestamp": timestamp,
            "properties": {
                "securityRules": [
                    {
                        "name": rule.name,
                        "priority": rule.properties.priority,
                        "direction": rule.properties.direction,
                        "access": rule.properties.access,
                        "protocol": rule.properties.protocol,
                        "sourceAddressPrefix": rule.properties.source_address_prefix,
                        "sourcePortRange": rule.properties.source_port_range,
                        "destinationAddressPrefix": rule.properties.destination_address_prefix,
                        "destinationPortRange": rule.properties.destination_port_range,
                    }
                    for rule in (nsg.security_rules or [])
                ],
                "defaultSecurityRules": [
                    {"name": r.name, "priority": r.properties.priority}
                    for r in (nsg.default_security_rules or [])
                ],
            },
            "tags": nsg.tags,
        }
        container.upsert_item(body=snapshot)
        print(f"[NSG] Snapshotted {nsg.name} at {timestamp}")


if __name__ == "__main__":
    sub_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    if not sub_id:
        print("AZURE_SUBSCRIPTION_ID required")
        sys.exit(1)
    snapshot_nsg(sub_id)
