---
description: "Query AWS CloudWatch metrics, alarms, PromQL and Logs Insights for EKS incident investigation."
---

# cloudwatch

Runs the AWS Labs CloudWatch MCP server in `agent-mcps`, with no ingress.
Agent Studio reaches it through
`mcp-cloudwatch.agent-mcps.svc.cluster.local`, and the pod reaches AWS through
the EKS Pod Identity associated with the `mcp-cloudwatch` ServiceAccount.
There is no credential or caller header on this entry.

Upstream `0.1.8` starts as stdio and exposes no transport flag. The chart in
argocd-env-demo pins that image and replaces its command with a small Python
launcher that imports the same registered tool object and runs it as stateless
streamable HTTP. Changing the image version therefore requires an import and
Helm render check, not just a tag bump.

`pod-role--mcp-cloudwatch` is declared in terraform-env-demo. Its policy is
limited to `ap-northeast-2` and to alarm reads, metric reads and discovery, log
group and anomaly discovery, and the start/get/stop calls that implement Logs
Insights queries. Start and stop do not mutate log data, but query scans incur
CloudWatch cost; callers should keep log groups, time windows and result limits
narrow.

This server sees CloudWatch telemetry, not arbitrary AWS resource state. It can
correlate AWS metrics, alarms and shipped logs with a cluster incident, but it
cannot by itself confirm an EC2 capacity event, subnet or ENI state, EBS
attachment state, ELB target health, IAM evaluation or CloudTrail event.

Upstream: https://github.com/awslabs/mcp/tree/main/src/cloudwatch-mcp-server
