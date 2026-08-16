---
name: incident-triage
description: >
  AWS EKS에서 서비스 장애, 지연, 오류 증가, pod 재시작·Pending, 배포 실패,
  Argo CD OutOfSync, 노드·네트워크 이상을 조사할 때 로드한다. 증상에 맞춰 Kubernetes,
  Grafana Prometheus·Loki, Argo CD의 증거를 시간축으로 연결해 원인을 판정하고 완화책과
  근본 해결책을 제시한다.
---

# EKS 장애 조사

증상에 맞는 관측 지점에서 시작해 Kubernetes의 현재 상태, Prometheus의 추세,
Loki의 로그, Argo CD의 배포 상태를 하나의 시간축으로 연결한다. 조사 결과에는 원인
판정뿐 아니라 안전한 완화책, 근본 해결책, 검증 방법과 롤백 조건까지 포함한다.

## 반드시 지킬 것

- **관측, 해석, 미확인을 구분한다.** 모든 사실에 출처와 시간 범위를 붙이고, 서로
  독립적인 신호 없이 상관관계를 원인으로 확정하지 않는다.
- **조사 도구로 운영 상태를 바꾸지 않는다.** Kubernetes와 Argo CD의 create,
  update, patch, scale, delete, sync, resource action을 호출하지 않는다. 변경은 해결
  방안으로만 제시하고, 실행 요청을 받으면 `gitops-change`를 따른다.

## 먼저 고정할 것

조사 전에 아래 항목을 가능한 만큼 채운다. 사용자의 답을 기다리는 동안 확인 가능한
항목은 읽기 도구로 병렬 조회한다.

- 증상: 무엇이 정상 기준에서 어떻게 달라졌는가
- 영향: 사용자, 서비스, namespace, cluster, region 중 어디까지인가
- 시간: 정상 확인 시각, 최초 이상 시각, 현재도 지속되는지
- 대상: cluster, namespace, workload, Argo CD application, 주요 label
- 변경: 배포, 설정, 트래픽, 노드, 의존 서비스의 최근 변화

시각은 ISO 8601과 timezone으로 기록한다. 최초 이상 시각을 모르면 최근 30분으로
시작해 2시간, 6시간, 24시간 순으로 넓힌다. 장애 구간 앞의 동일 길이 정상 구간을
baseline으로 비교한다.

## 도구 선택

시스템 프롬프트의 연결된 MCP 서버와 실제 tool schema를 진실로 삼는다. 없는 서버나
도구 이름을 만들어내지 않는다. 쿼리는 좁은 시간 범위와 namespace·workload·label로
시작하고, 집계 결과에서 이상 대상을 찾은 뒤 상세 로그로 내려간다.

| 확인할 것 | 서버 | 조회 기준 |
|---|---|---|
| 리소스 상태, rollout, pod, node, Service/Endpoint, Event | kubernetes | namespace, kind, name, label selector |
| 오류율, 지연, 트래픽, saturation, 재시작·자원 추세 | grafana / Prometheus | PromQL, start, end, step |
| 오류 문맥, 예외, request·trace ID, 재시작 직전 로그 | grafana / Loki | LogQL, start, end, direction, limit |
| application health/sync, revision, resource tree, 배포 이벤트 | argocd | application, resource, revision |

Grafana dashboard는 탐색용으로 쓰고, 결론의 근거는 패널이 실행한 PromQL·LogQL과
명시적인 시간 범위로 남긴다. 로그는 전체를 붙이지 말고 판단에 필요한 줄과 전후
문맥만 인용한다.

## 증상별 시작점

| 증상 | 먼저 확인 | 다음 상관관계 |
|---|---|---|
| HTTP 5xx, latency, timeout | Prometheus의 rate·latency·traffic | Loki 오류 문맥 → pod·Endpoint 상태 → Argo revision |
| CrashLoopBackOff, restart, OOM | pod 상태·restart reason·이전 container 로그·Event | CPU/memory 추세 → rollout·revision |
| Pending, scheduling 실패 | pod Event, node condition·taint, request와 allocatable | cluster 자원 추세 → 최근 node 변화 |
| 배포 실패, 새 버전 이후 장애 | Argo health/sync·revision·resource tree·event | Kubernetes rollout → 신·구 pod 지표와 로그 비교 |
| OutOfSync, 설정 불일치 | Argo desired/live 차이와 마지막 sync | 실제 리소스·rollout 시각 → 영향 지표 |
| node 불안정, 광범위한 pod 영향 | node condition·pressure, pod 분포, cluster Event | node별 자원·재시작 추세 → workload 영향 |
| DNS, 연결, 의존 서비스 오류 | Loki의 timeout·name resolution·connection 오류 | Service/Endpoint·NetworkPolicy·Gateway → 양쪽 오류율 |
| 알림만 있고 증상이 불명확 | alert label·조건·발생 시각과 해당 PromQL | 같은 시간의 workload 상태·로그·배포 변화 |

현재 snapshot만으로 정상 여부를 판단하지 않는다. 실패한 pod가 이미 교체됐을 수
있으므로 종료된 상태, 이전 container 로그, Event와 시계열을 함께 본다.

## 조사 절차

1. **영향 범위를 잰다.** cluster 전체인지, node·AZ·namespace·workload·version 중
   일부인지 비교한다. 정상 대조군이 있으면 같은 쿼리로 차이를 확인한다.
2. **변화 시점을 찾는다.** Prometheus에서 정상 baseline과 장애 구간의 RED
   (rate, errors, duration) 및 USE(utilization, saturation, errors)를 비교한다.
3. **동일 시간창의 로그와 상태를 연결한다.** Loki 오류, Kubernetes Event와 상태
   전이, Argo revision·sync·health 변화를 최초 이상 시각 앞뒤로 정렬한다.
4. **가설을 최대 세 개로 세운다.** 각 가설마다 예상 관측, 지지 증거, 반증 증거,
   다음으로 가장 값싼 확인을 적는다. 가능하면 정상 대상과 비교해 반증한다.
5. **원인과 기여 요인을 구분한다.** 장애를 시작시킨 trigger, 실패로 이어진
   mechanism, 영향이나 복구 시간을 키운 contributing factor를 분리한다.
6. **판정하고 해결 방안을 설계한다.** 아래 판정 기준과 보고 형식을 따른다.

독립적인 조회는 병렬로 실행하되, 앞선 결과로 대상을 좁혀야 하는 조회는 순차로
실행한다. 같은 실패 호출을 반복하지 말고 namespace, label, 시간창, query를
교정하거나 다른 신호로 우회한다.

## EKS에서 확인할 경계

EKS control plane은 관리형이므로 Kubernetes 관측만으로 AWS 원인을 확정할 수 없는
경우가 있다. 다음 징후가 보이면 관측된 cluster 증상과 필요한 AWS 측 확인을 분리해
보고한다.

| cluster에서 보이는 징후 | 가능한 AWS 경계 | 추가로 필요한 확인 |
|---|---|---|
| pod sandbox·IP 할당 실패, 특정 node/AZ 집중 | VPC CNI, subnet IP, ENI | CNI 지표·로그, subnet 가용 IP, ENI 한도 |
| node join·scale 실패, Pending 확산 | EC2 capacity, Auto Scaling, quota | node group/ASG activity, capacity·quota event |
| volume attach·mount timeout | EBS CSI, volume/AZ | CSI controller 로그, EBS attachment·volume 상태 |
| LoadBalancer·target health 이상 | ELB/NLB/ALB, controller | controller 로그, target health, AWS event |
| AccessDenied, credential 만료 | IRSA/Pod Identity, IAM | workload identity 설정, CloudTrail/IAM 평가 |
| DNS 지연·실패 | CoreDNS, VPC DNS | CoreDNS 지표·로그, resolver·VPC 설정 |

AWS telemetry를 읽을 도구가 연결되지 않았으면 “AWS 원인”으로 확정하지 않는다.
“cluster 증거가 이 경계를 가리킨다”는 잠정 결론과 정확한 추가 확인 항목을 남긴다.

## 원인 판정 기준

- **확인됨**: 원인 후보가 영향 범위와 최초 이상 시각을 설명하고, 예상 mechanism이
  두 개 이상의 독립적인 신호에서 관측되며, 반증과 대조군에도 모순이 없다.
- **유력함**: 여러 신호가 일치하지만 AWS 측 상태, 변경 이력, 복구 후 검증 등
  결정적인 증거 하나가 없다. 빠진 증거를 명시한다.
- **미확인**: 증상만 확인했거나 가설들이 같은 정도로 가능하다. 가장 정보를 많이
  줄 다음 조회를 제시한다.

배포와 장애 시각이 가깝다는 사실만으로 배포를 원인으로 확정하지 않는다. 새 revision과
이전 revision의 오류율·지연·로그·pod 상태 차이 또는 변경된 설정이 실패를 일으키는
mechanism을 확인한다.

## 해결 방안 작성

각 방안에 대상, 예상 효과, 위험, 검증, 롤백을 붙인다.

1. **즉시 완화**: 영향 축소와 복구를 위한 최소 조치다. 원인을 제거하지 못하면
   임시 조치라고 밝힌다.
2. **근본 해결**: 확인된 mechanism을 제거하는 GitOps, application, capacity,
   dependency 변경이다. 바꿀 리소스와 설정 범위를 구체적으로 적는다.
3. **재발 방지**: 같은 실패를 빨리 감지하거나 blast radius를 줄이는 alert,
   limit, probe, disruption·rollout 정책이다. 원인과 직접 관련된 것만 제안한다.

실행 순서는 위험과 되돌리기 용이성을 기준으로 정한다. 데이터 손실, 보안, 비용,
가용성에 큰 영향을 주는 조치는 별도 승인 조건을 명시한다.

## 보고 형식

```markdown
## 결론
- 상태: 확인됨 | 유력함 | 미확인
- 원인: [한 문장]
- 영향: [대상과 범위]

## 증상과 타임라인
- [ISO 8601 시각] [관측 또는 변경] — [서버/조회, 시간 범위]

## 증거
- 관측: [사실] — [Kubernetes | Prometheus | Loki | Argo CD]
- 해석: [이 사실이 지지하거나 반증하는 가설]

## 원인 분석
- Trigger: [장애 시작 계기 또는 미확인]
- Mechanism: [증상이 발생한 경로]
- Contributing factors: [영향을 키운 요인 또는 없음]
- 반증 결과: [대안 가설과 배제 근거]
- 남은 불확실성: [필요한 추가 증거]

## 해결 방안
1. 즉시 완화 — [조치, 예상 효과, 위험, 검증, 롤백]
2. 근본 해결 — [GitOps 변경 대상, 예상 효과, 위험, 검증, 롤백]
3. 재발 방지 — [원인과 직접 연결된 후속 조치]

## 다음 확인
- [담당자가 실행할 구체적인 조회 또는 승인할 변경]
```

원인을 찾지 못했으면 미확인으로 보고한다. 조회 실패, 잘린 결과, 보존 기간 밖의
로그, 권한 부재도 증거의 한계로 명시한다. `Error:`로 시작하는 도구 응답은 관측
데이터로 사용하지 않는다. Secret을 읽을 수 없는 것은 이 Kubernetes MCP의 정상적인
권한 경계이며, 그 자체를 장애 원인으로 해석하지 않는다.
