# Kube SRE 구성

Grafana 알림과 사용자 질문을 읽기 전용으로 조사하고 대응 방법을 안내하는 프로필이다.
시스템 프롬프트는 [kube-sre.md](prompts/kube-sre.md)를 사용한다. 운영 변경을 실행하는
Agent와 역할을 분리하고 `incident-triage`를 명시적으로 연결한다. CI 조사도 담당하면
`ci-failure-investigator`와 읽기 전용 GitHub 도구를 추가한다.

## 도구 범위

MCP 서버가 도구를 제공한다는 사실과 해당 Agent에 제공할 범위는 구분한다. Agent의
바인딩에 실제 발견한 조회 도구 이름을 명시한다. 빈 선택은 모든 도구를 뜻하므로 읽기 전용
설정으로 사용하지 않는다. 동적 발견은 끄고 다른 MCP의 변경 도구가 추가되지 않도록 한다.

| 서버 | 이 프로필의 도구 |
|---|---|
| Kubernetes | `events_list`, `namespaces_list`, `nodes_log`, `nodes_stats_summary`, `nodes_top`, `pods_get`, `pods_list`, `pods_list_in_namespace`, `pods_log`, `pods_top`, `resources_get`, `resources_list` |
| Argo CD | `list_applications`, `list_clusters`, `get_application`, `get_appproject`, `get_application_resource_tree`, `get_application_managed_resources`, `get_application_workload_logs`, `get_application_events`, `get_resource_events`, `get_resources`, `get_resource_actions` |
| Grafana | `check_datasources_health`, `get_annotations`, `get_dashboard_by_uid`, `get_dashboard_panel_queries`, `get_dashboard_property`, `get_dashboard_summary`, `get_datasource`, `list_datasources`, `list_loki_label_names`, `list_loki_label_values`, `list_prometheus_label_names`, `list_prometheus_label_values`, `list_prometheus_metric_metadata`, `list_prometheus_metric_names`, `query_loki_logs`, `query_loki_patterns`, `query_loki_stats`, `query_prometheus`, `query_prometheus_histogram`, `search_dashboards`, `search_folders` |

`resources_scale`, exec, apply, delete, Argo CD sync와 리소스 실행은 제외한다. Grafana의
`alerting_manage_rules`, `alerting_manage_routing`, `grafana_api_request`는 조회와 변경을
함께 제공할 수 있으므로 쓰기가 켜진 공유 서버에서는 제외한다. 알림 본문과 metric으로
조사하되 규칙 조회가 필요한데 제공되지 않으면 한계를 알린다. 해당 도구를 추가하려면
설치 버전의 서버가 읽기 전용 모드에서 변경을 거절하는지 먼저 검증한다.

GitHub는 [코딩 프로필](code-agent.md#github-mcp-프로필)의 `X-MCP-Readonly: true`와
`X-MCP-Toolsets: context,repos,issues,pull_requests,actions`를 적용하고 실제 읽기 도구를
다시 발견한다. 필요한 commit·파일·PR·Actions 조회만 선택한다. 자격 증명을 복사하거나
권한을 확장하지 않는다. 리소스 읽기는 여전히 민감한 정보를 포함할 수 있으므로 서버의
RBAC와 Agent 공개 범위도 설치 대상에 맞춰 유지한다.

## Slack

전용 Slack 앱을 연결하고 호스트 앱이 표시하는 Agent 이벤트 URL을 사용한다.
Channel keywords에 `[firing:`을 설정하면 대소문자 구분 없이 Grafana의 `[FIRING:1]`
제목을 감지한다. `[RESOLVED]`는 이 키워드와 일치하지 않는다. 일반 질문은 @mention,
DM 또는 Agent가 응답한 스레드의 사람 후속 질문으로 받는다.

키워드는 봇이 초대된 채널에 적용되며 특정 채널을 지정하는 설정은 아니다.
Slack 앱의 이벤트 구독과 채널 참여를 확인하고 테스트 채널에서 먼저 검증한다.
동일 키워드를 다른 범용 Agent에도 설정하면 각 Agent가 별도로 응답할 수 있다.

검증은 합성 알림임을 명시한 메시지로 키워드 호출·실제 MCP 조회·원본 스레드 응답을
확인한다. 이어서 같은 스레드의 질문과 @mention을 확인하고 운영 리소스에 변경이 없었는지
트레이스로 검증한다. 테스트 메시지는 실제 장애나 복구의 증거로 사용하지 않는다.
