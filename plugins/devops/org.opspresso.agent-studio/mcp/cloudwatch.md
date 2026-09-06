---
description: >
  Investigate AWS/EKS metrics, alarms and logs through CloudWatch, PromQL and
  Logs Insights using the deployment's default credentials without profile_name.
  Query scans incur cost; this provides telemetry, not EC2/subnet/ENI state,
  ELB target health, IAM evaluation or CloudTrail events.
---

# cloudwatch

## Connection and AWS access

The service runs in `agent-mcps` without ingress. Its internal suffix must
be allowed by `MCP_INTERNAL_HOST_SUFFIXES`. No caller credential is configured;
the `mcp-cloudwatch` ServiceAccount uses EKS Pod Identity to access AWS.

Terraform's `pod-role--mcp-cloudwatch` policy is limited to `ap-northeast-2`:
alarm and metric reads, log-group and anomaly discovery, and Logs Insights
start/get/stop operations. Queries do not mutate log data but incur scan costs.
Narrow log groups and time windows to reduce scanned data. Query limits reduce
returned rows; they do not cap scan cost.

## Deployment and verification

The argocd-env-demo chart pins upstream `0.1.8`, whose entrypoint is stdio.
A Python launcher imports its registered tools and exposes stateless streamable
HTTP. Image upgrades require an import check and Helm render check.

Verify an actual permitted AWS read after changing the image, identity or IAM
policy. A working MCP connection does not establish AWS authorization.

This integration covers CloudWatch telemetry, not arbitrary AWS resource state.
EC2 capacity events, subnet/ENI state, EBS attachments, ELB target health, IAM
evaluation and CloudTrail events require separate access.

Upstream: https://github.com/awslabs/mcp/tree/main/src/cloudwatch-mcp-server
