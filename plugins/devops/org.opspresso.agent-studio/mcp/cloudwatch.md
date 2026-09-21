---
description: >
  Query AWS CloudWatch metrics, alarms and collected logs. Query scans can incur cost; telemetry does not establish arbitrary AWS resource state. Account, region and credential selection follow the configured connection.
---

# cloudwatch

Bundled endpoint: `http://mcp-cloudwatch.agent-mcps.svc.cluster.local/mcp`.
The `argocd-env-demo` k3s deployment exposes AWS Labs CloudWatch MCP through
Streamable HTTP inside the cluster. See
[in-cluster MCP setup](../../../../docs/agent-studio.md#in-cluster-mcp-services)
for network access, plugin sync and agent bindings.

Choose the account, region and credential source on the installing side; these
may be workload identity, a role or another supported credential chain. Do not
copy a profile name, IAM policy or region from another installation.

Limit permissions to the required telemetry operations. Narrow log groups and
time windows before starting a query. A result-row limit does not cap scan cost.
CloudWatch evidence does not replace EC2, subnet, ENI, volume attachment, load
balancer target health, IAM evaluation or CloudTrail access.

If adapting a stdio server to remote HTTP, verify the adapter against the chosen
upstream version. Test an authorized AWS read after credential or image changes;
MCP discovery alone does not establish account access.

Upstream: https://github.com/awslabs/mcp/tree/main/src/cloudwatch-mcp-server
