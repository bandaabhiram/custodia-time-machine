"""
Key Vault Collector — Captures network rules, access policies, and certificate state.
"""
import os
import sys
from datetime import datetime, timezone

from azure.identity import DefaultAzureCredential
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.cosmos import CosmosClient


def get_cosmos_container():
    client = CosmosClient(
        os.environ["COSMOS_ENDPOINT"],
        credential=os.environ["COSMOS_KEY"]
    )
    db = client.get_database_client("security-snapshots")
    return db.get_container_client("config-snapshots")


def snapshot_keyvaults(subscription_id: str):
    credential = DefaultAzureCredential()
    kv_client = KeyVaultManagementClient(credential, subscription_id)
    container = get_cosmos_container()
    timestamp = datetime.now(timezone.utc).isoformat()

    for vault in kv_client.vaults.list():
        snapshot = {
            "id": f"{vault.id}__{timestamp}",
            "subscriptionId": subscription_id,
            "resourceType": "Microsoft.KeyVault/vaults",
            "resourceId": vault.id,
            "resourceName": vault.name,
            "timestamp": timestamp,
            "properties": {
                "enableRbacAuthorization": vault.properties.enable_rbac_authorization,
                "enableSoftDelete": vault.properties.enable_soft_delete,
                "softDeleteRetentionInDays": vault.properties.soft_delete_retention_in_days,
                "networkAcls": {
                    "defaultAction": vault.properties.network_acls.default_action if vault.properties.network_acls else None,
                    "bypass": vault.properties.network_acls.bypass if vault.properties.network_acls else None,
                    "ipRules": [r.value for r in (vault.properties.network_acls.ip_rules or [])] if vault.properties.network_acls else [],
                    "virtualNetworkRules": [r.id for r in (vault.properties.network_acls.virtual_network_rules or [])] if vault.properties.network_acls else [],
                },
                "accessPolicies": [
                    {
                        "tenantId": p.tenant_id,
                        "objectId": p.object_id,
                        "permissions": {
                            "keys": p.permissions.keys,
                            "secrets": p.permissions.secrets,
                            "certificates": p.permissions.certificates,
                        }
                    }
                    for p in (vault.properties.access_policies or [])
                ] if not vault.properties.enable_rbac_authorization else [],
            },
        }
        container.upsert_item(body=snapshot)
        print(f"[KV] Snapshotted {vault.name}")


if __name__ == "__main__":
    sub_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    if not sub_id:
        print("AZURE_SUBSCRIPTION_ID required")
        sys.exit(1)
    snapshot_keyvaults(sub_id)
