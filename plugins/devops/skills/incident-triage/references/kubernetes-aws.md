# Kubernetes와 AWS 관측

대상이 Kubernetes 또는 AWS일 때만 이 자료를 읽는다. 클러스터가 EKS인지, 실제로 연결된
서버와 수집된 데이터가 무엇인지 확인한다. 아래 제품명은 관측 역할의 예이며 필수 조합이 아니다.

| 확인할 것 | 사용 가능한 예 | 조회 기준 |
|---|---|---|
| 리소스·rollout·Event·이전 컨테이너 로그 | Kubernetes | namespace, kind, name, label |
| 오류율·지연·트래픽·포화도 추세 | Grafana / Prometheus | query, start, end, step |
| 오류 문맥·request/trace ID | Loki 또는 수집된 로그 | query, start, end, limit |
| AWS 지표·알람·수집 로그 | CloudWatch | region, metric namespace, log group |
| desired/live 차이·revision·배포 이벤트 | Argo CD 또는 설치된 GitOps 컨트롤러 | application, revision, resource |

실패한 Pod는 교체됐을 수 있으므로 현재 snapshot만으로 정상이라고 판단하지 않는다.
대시보드는 탐색에 쓰고 근거에는 원본 쿼리와 시간창을 남긴다. CloudWatch의 인증 방식·region은
설치 설정을 따른다. 기본 credential chain을 쓰는 배포에서는 임의의 profile을 지정하지 않는다.
Logs Insights는 log group과 시간창으로 스캔 비용을 줄인다. 결과 limit은 스캔 비용 상한이 아니다.

## EKS에서 확인할 경계

EKS control plane은 관리형이므로 Kubernetes 관측만으로 AWS 원인을 확정할 수 없는
경우가 있다. `cloudwatch`가 연결돼 있으면 같은 시간창의 alarm, metric, log를 먼저
확인한다. 다음 징후가 보이면 관측된 cluster 증상, CloudWatch 증거, 남은 AWS resource
상태 확인을 분리해 보고한다.

| cluster에서 보이는 징후 | 가능한 AWS 경계 | CloudWatch에서 확인 | 남는 확인 |
|---|---|---|---|
| pod sandbox·IP 할당 실패, 특정 node/AZ 집중 | VPC CNI, subnet IP, ENI | CNI·container 로그, node network metric·alarm | subnet 가용 IP, ENI 한도·상태 |
| node join·scale 실패, Pending 확산 | EC2 capacity, Auto Scaling, quota | node 수·자원 metric, 관련 alarm·log | node group/ASG activity, capacity·quota event |
| volume attach·mount timeout | EBS CSI, volume/AZ | EBS metric·alarm, CSI controller 로그 | attachment·volume 상태 |
| LoadBalancer·target health 이상 | ELB/NLB/ALB, controller | request·target 오류 metric·alarm, controller 로그 | target health와 LB 설정 |
| AccessDenied, credential 만료 | IRSA/Pod Identity, IAM | workload의 AccessDenied 로그 | CloudTrail event와 IAM policy 평가 |
| DNS 지연·실패 | CoreDNS, VPC DNS | CoreDNS metric·log가 수집됐다면 오류 추세 | resolver·VPC DNS 설정 |

CloudWatch MCP는 metric, alarm, 수집된 log를 읽지만 EC2, EKS, Auto Scaling, EBS,
ELB, IAM, CloudTrail의 resource 상태 API는 제공하지 않는다. 그 상태를 읽을 도구가
연결되지 않았으면 “AWS 원인”으로 확정하지 않고, “증거가 이 경계를 가리킨다”는
잠정 결론과 정확한 추가 확인 항목을 남긴다.

Secret 읽기나 exec의 허용 여부는 실제 RBAC로 확인한다. 권한 부재 자체를 장애 원인으로
해석하거나 다른 계정·도구로 우회하지 않는다.
