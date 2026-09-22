# 오디오 도우미 구성

Plaud 녹음의 원본 보관·전사·요약을 하나의 Agent와 AudioJob worker로 처리한다.
[시스템 프롬프트](prompts/audio-agent.md)를 사용하고 `audio-processing`을 명시적으로 연결한다.
회의록 양식이 필요하면 `meeting-minutes`, 문장 편집이 필요하면 `korean-humanize`를 추가한다.

설치에서 확인할 조건:

- Agent의 오디오 처리 도구, Plaud MCP 연결과 `get_file`의 source_ref 매핑.
- Models에 등록된 **transcription** 모델과 실제로 접근 가능한 provider endpoint·credential.
  채팅 모델 등록이나 과거 AudioJob 성공 이력만으로 현재 전사 모델의 준비를 판단하지 않는다.
- 프로젝트 AudioJob config의 전사 모델·언어·보존 기간·동시 접수 한도와 후처리 projectName.
  후처리는 같은 Agent의 현재 설정을 사용하며 versionName을 전달하지 않는다.
- 비공개 파일 저장소와 audio-worker. EKS의 S3·Pod Identity와 k3s의 MinIO 연결은 각 설치 설정이다.

먼저 config와 Plaud 읽기 도구를 확인한 뒤, 사용자가 지정한 녹음 한 건으로 원본·전사·요약
Artifact의 실제 내용을 확인한다. 같은 요청을 반복했을 때 기존 job과 결과를 재사용하는지도 확인한다.
계정 연결은 테스트·운영에서 각각 확인하며 OAuth token을 다른 설치로 복사하지 않는다.
정기 수집은 별도 schedule trigger와 scan ticker가 활성화돼야 한다. 배포 health만으로 처리 성공을 판정하지 않는다.
