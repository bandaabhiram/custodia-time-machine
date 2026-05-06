# Incident Response Playbook

## Scenario: "The SQL firewall was changed at 2:47 AM"

### Step 1: Identify the resource
```bash
python queries/cosmos_queries/drift_detection.py \
  --resource-type Microsoft.Sql/servers/firewallRules \
  --days 1
```

### Step 2: Query the timeline
```bash
python queries/cosmos_queries/forensic_query.py \
  --resource-id "/subscriptions/xxx/.../sql-server" \
  --start "2024-05-05T00:00:00Z" \
  --end "2024-05-06T06:00:00Z"
```

### Step 3: Correlate with Activity Log
```kusto
AzureActivity
| where ResourceId == "TARGET_RESOURCE_ID"
| where OperationNameValue contains "firewallRules"
| project TimeGenerated, Caller, OperationNameValue, Properties
```

### Step 4: Reconstruct before/after
Compare the two closest snapshots around the change time. The full state is in `properties`.
