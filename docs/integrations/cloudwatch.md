---
description: >
  Query AWS CloudWatch metrics, alarms and collected logs. Query scans can incur cost; telemetry does not establish arbitrary AWS resource state. Account, region and credential selection follow the configured connection.
---

# cloudwatch

Operator reference for a separately registered integration. This file is not
auto-synced as a bundled MCP declaration. Use the description as a starting
point and adjust it to the deployed tools and permission boundary.

Deploy or connect a CloudWatch MCP implementation and register its actual endpoint.
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
