"""
Drift Detection CLI — Query the time-machine for configuration changes.

Usage:
    python drift_detection.py --resource-type Microsoft.Network/networkSecurityGroups --days 7
"""
import argparse
import json
import os
from datetime import datetime, timedelta, timezone

from azure.cosmos import CosmosClient


def main():
    parser = argparse.ArgumentParser(description="Detect config drift in Custodia")
    parser.add_argument("--resource-type", required=True)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--subscription-id", default="*")
    args = parser.parse_args()

    client = CosmosClient(
        os.environ["COSMOS_ENDPOINT"],
        credential=os.environ["COSMOS_KEY"]
    )
    container = client.get_database_client("security-snapshots").get_container_client("config-snapshots")

    since = (datetime.now(timezone.utc) - timedelta(days=args.days)).isoformat()

    query = """
        SELECT c.resourceName, c.resourceId, c.timestamp, c.properties
        FROM c
        WHERE c.resourceType = @rt
          AND c.timestamp > @since
        ORDER BY c.resourceId, c.timestamp DESC
    """
    params = [
        {"name": "@rt", "value": args.resource_type},
        {"name": "@since", "value": since},
    ]

    results = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
    print(f"Found {len(results)} snapshots for {args.resource_type} in last {args.days} days")

    # Simple drift detection: compare consecutive snapshots
    by_resource = {}
    for r in results:
        by_resource.setdefault(r["resourceId"], []).append(r)

    for rid, snapshots in by_resource.items():
        if len(snapshots) < 2:
            continue
        latest = snapshots[0]["properties"]
        previous = snapshots[1]["properties"]
        if json.dumps(latest, sort_keys=True) != json.dumps(previous, sort_keys=True):
            print(f"\n🚨 DRIFT DETECTED: {snapshots[0]['resourceName']}")
            print(f"   Changed between {snapshots[1]['timestamp']} and {snapshots[0]['timestamp']}")


if __name__ == "__main__":
    main()
