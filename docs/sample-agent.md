# 다목적 Agent 구성

[sample-agent.md](prompts/sample-agent.md)의 시스템 프롬프트를 사용하고 요청마다 필요한
기능 찾기(`dynamicCapabilities`)를 활성화한다. 동적 발견은 설치된 카탈로그에서 요청과
맞는 기능을 제공하며 모든 도구나 개인 OAuth 연결을 자동으로 허가하지 않는다.

항상 필요한 바인딩만 명시적으로 연결하고 나머지는 실제 발견 결과로 사용한다. Memory를
먼저 회상하려면 `memoryRecall`과 `recall`을 허용하는 Memory MCP 바인딩이 함께 필요하다.
Memory를 읽을 수 있다는 사실은 임의의 지속 저장 허가가 아니다.

URL 읽기, 이미지, Slack 읽기는 설치 대상의 사용 범위에 맞게 켠다. Workspace와 오디오는
각 전용 Agent의 설정·Worker·접근 정책이 필요하므로 범용 Agent에 기능 이름만 추가해서
사용 가능하다고 가정하지 않는다. 파일 생성·편집은 호스트 앱의 builtin과 Artifact 저장소를
사용한다.

Slack에서 Grafana 알림을 Kube SRE가 맡는다면 이 Agent의 Channel keywords에는 같은
`[firing:`을 넣지 않는다. @mention·DM·기존 스레드 질문은 계속 받을 수 있다.

검증은 서로 다른 작업에서 실제 Skill 선택, 필요한 도구 호출, Artifact 저장을 확인한다.
도구가 없는 작업의 한계도 확인하며, 텍스트의 완료 주장만으로 실행 성공을 판정하지 않는다.
