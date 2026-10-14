# 오디오 도우미 구성

Studio의 한 Agent가 AudioJob으로 Plaud 수집을 조율한다. Librio는 원본 보관·전사·회의록과 그 검색 문서를 소유한다. Studio는 원본 전송·작업 진행·비용 확인과 결과 읽기 중계를 담당한다.
[시스템 프롬프트](prompts/audio-agent.md)를 사용하고 `audio-processing`을 명시적으로 연결한다.
회의록 양식이 필요하면 `meeting-minutes`, 문장 편집이 필요하면 `korean-humanize`를 추가한다.

## 설치 조건

- Agent의 오디오 처리 도구, Plaud MCP 연결과 `get_file`의 source_ref 매핑.
- Librio가 허용한 **transcription** 연결의 공개 모델 ID와 Librio 서버의 endpoint·credential.
  채팅 모델 등록이나 과거 AudioJob 성공 이력만으로 현재 전사 모델의 준비를 판단하지 않는다.
- Agent AudioJob config의 전사 모델·언어·보존 기간·동시 접수 한도와 선택적 회의록(summary) 모델·지시문.
- Librio 비공개 원본 저장소와 audio worker, Studio→Librio 서명 위임과 현재 사용자 바인딩.
  EKS의 S3·Pod Identity와 k3s의 MinIO 연결은 각 설치 설정이다.
- 회의록은 Librio의 **summary** 연결을 사용한다. embedding·decision·전사 모델을 회의록 모델로
  선택하지 않는다. catalogId와 provider wireId는 공개 연결 ID와 다르며 가격 누락은 unknown이다.

## 처리 결과 확인

먼저 config와 Plaud 읽기 도구를 확인한 뒤, 사용자가 지정한 녹음 한 건으로 원본 Artifact와
`AudioJob read`의 전사문·회의록 실제 내용을 확인한다. 같은 요청을 반복했을 때 기존 job과 결과를 재사용하는지도 확인한다.
계정 연결은 테스트·운영에서 각각 확인하며 OAuth token을 다른 설치로 복사하지 않는다.
정기 수집은 별도 schedule trigger와 scan ticker가 활성화돼야 한다. 배포 health만으로 처리 성공을 판정하지 않는다.

전사문·회의록은 Librio가 검색 문서로 직접 발행한다. Studio는 이를 복사하거나 다시 수집하지 않는다. 사용자가 별도로 요청한 장기 선호·결정 기록은 Memory에 저장한다. Plugin 설치만으로 서비스·계정·공간·기록 권한이 생기지 않는다.
