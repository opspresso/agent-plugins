# 오디오 도우미 구성

Studio의 한 Agent가 Agent Knowledge MCP로 녹음 처리를 위임한다. Agent Knowledge는 오디오 설정(profile)·원본·전사·회의록·작업 이력과
검색 문서를 소유한다. Studio는 Chat 파일을 짧은 시간만 유효한 참조로 Agent Knowledge에 전달하고, 완료된 결과를 원래 Chat에 한 번 전달한다.
[시스템 프롬프트](prompts/audio-agent.md)를 사용하고 `audio-processing`을 명시적으로 연결한다.
회의록 양식이 필요하면 `meeting-minutes`, 문장 편집이 필요하면 `korean-humanize`를 추가한다.

## 설치 조건

- Studio 배포의 Agent Knowledge 연결(`KNOWLEDGE_URL`, `KNOWLEDGE_OIDC_CLIENT_ID`)과 Agent에 연결한 Agent Knowledge Tools 항목.
  Studio는 MCP 요청마다 현재 사용자에게 위임한 단기 token을 보낸다. 쓰기 도구에는 편집 가능한 사용자 등급이 필요하다.
- Agent Knowledge의 원본 저장소, audio worker, 허용된 전사(**transcription**)·회의록(**summary**) 모델.
  공급자 주소·credential·가격은 Models와 Agent Knowledge 설치 설정이다.
- 사용자별 오디오 profile. Agent Knowledge 콘솔의 오디오 설정에서 전사 모델·선택 회의록 모델과 지시문·언어·보존 기간·
  작업 수 한도를 저장하고 기본 profile을 선택한다. Studio Tools의 Agent Knowledge 상세 화면에 설정·이력 링크가 있다.
- 비동기 결과 전달에는 인증된 schedule tick(`/api/triggers/scan`)이 필요하다. tick이 없으면 결과가 Chat에 전달되지 않는다.

## 입력 경로

- Chat에 첨부한 녹음(녹음 첨부 한도 512 MiB 이하)은 파일 ID로 `recording_import`에 전달된다.
- 더 큰 녹음은 Agent Knowledge 콘솔에서 올린다. Agent는 `audio_list`로 녹음을 찾아 작업을 제출한다.
- Plaud MCP의 `source_ref`를 받는 도구는 현재 없다. Plaud 녹음의 자동 수집·처리는 지원하지 않는다.

## 처리 결과 확인

녹음 한 건을 Chat에 첨부해 처리를 요청한다. 다음을 확인한다.

1. 응답에 Agent Knowledge 작업 ID와 접수 상태가 있고, 같은 요청을 반복해도 새 작업이 생기지 않는다.
2. 완료 뒤 원래 Chat에 결과가 전달되고 전사문·회의록이 Chat 파일로 저장된다.
3. Agent Knowledge 콘솔의 녹음 화면에 같은 작업과 사용한 profile·모델이 기록된다.
4. Agent Knowledge 검색 도구로 해당 회의 내용을 찾을 수 있다.

배포 health만으로 처리 성공을 판정하지 않는다. 계정 연결은 테스트·운영에서 각각 확인하며 token을 다른 설치로 복사하지 않는다.
Studio는 전사문·회의록을 다시 수집하지 않는다. 사용자가 별도로 요청한 장기 선호·결정 기록은 Memory에 저장한다.
Plugin 설치만으로 서비스·계정·기록 권한이 생기지 않는다.
