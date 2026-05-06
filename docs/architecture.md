# Custodia Architecture

## Data Flow

1. **Event Grid** subscribes to Azure Activity Logs at the subscription level
2. On any `ResourceWriteSuccess` or `ResourceDeleteSuccess`, Event Grid pushes an event to the Function App
3. The **ActivityLogTrigger** function identifies the resource type and invokes the appropriate collector
4. Collectors call ARM/Graph APIs to fetch the **full current state** of the resource
5. State is flattened into a self-contained JSON document and upserted into Cosmos DB
6. A separate **polling trigger** (TimerTrigger, 15 min) catches any missed events

## Schema Design

Cosmos DB uses a single container with `subscriptionId` as the partition key. Each document is self-contained:

```json
{
  "id": "/subscriptions/xxx/resourceGroups/yyy/providers/.../__2024-05-06T12:00:00Z",
  "subscriptionId": "xxx",
  "resourceType": "Microsoft.Network/networkSecurityGroups",
  "resourceId": "...",
  "resourceName": "my-nsg",
  "timestamp": "2024-05-06T12:00:00Z",
  "properties": { ... full resource state ... }
}
```

This flattened design sacrifices relational queries for write throughput and simplicity.
