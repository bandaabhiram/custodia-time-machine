# Cost Analysis

## Monthly Estimate (Mid-Size Estate: 500 resources)

| Component | Cost |
|-----------|------|
| Cosmos DB (Serverless, 1 year TTL) | ~$80 |
| Azure Functions (Consumption) | ~$25 |
| Event Grid (1M events) | ~$0.60 |
| Application Insights | ~$15 |
| Power BI Embedded (A1) | ~$80 |
| **Total** | **~$200/month** |

## Cost Optimization

- Reduce TTL from 1 year to 90 days for non-critical resources: saves ~40%
- Use Cosmos DB autoscale instead of serverless for predictable workloads
- Archive old snapshots to Azure Blob (cool tier) instead of Cosmos DB
