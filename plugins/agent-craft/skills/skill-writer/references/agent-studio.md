# Agent Studio 스킬 배포

이 저장소에 기여하거나 Agent Studio에 동기화하는 스킬을 작성할 때 읽는다.

## Agent Studio 계약

- 스킬은 `plugins/<plugin>/skills/<skill>/SKILL.md`에서 발견된다. 스킬 디렉터리는 한 단계다.
- 시스템 프롬프트에는 연결된 스킬의 이름과 description이 표시된다. 본문은
  `Skill(skill_name="이름")` 호출로 읽는다. 연결된 목록과 실제 schema를 기준으로 작성한다.
- `Skill(skill_name="이름", file_path="references/example.md")`는 그 스킬 안의 파일만 읽는다.
  다른 스킬의 자료는 그 스킬이 연결돼 있을 때만 요청하고, 없을 때의 대안도 적는다.
- 참고 파일은 `.md`·`.txt`·`.json`·`.yaml`·`.yml`·`.csv`를 지원한다. 파일당 64KiB,
  스킬당 20개·합계 200KiB이며 `SKILL.md`는 첨부 한도에서 제외한다.
- 실행 스크립트와 바이너리는 동기화되지 않는다. 텍스트 템플릿은 Markdown 코드 블록으로 둔다.
- `GenerateImage`, `EditImage`, `SaveFile`, `File`, `FetchUrl`, 위임 도구는 런에서 제공될 때만 쓴다.
  `FetchUrl`은 버전의 `urlFetch` 설정이 필요하다. 쉘·파일시스템 접근을 가정하지 않는다.
- 플러그인 설치만으로 런에 제공되는 것은 아니다. 명시적 binding 또는 동적 발견으로
  현재 런에 제공된 목록을 확인한다. 같은 플러그인의 다른 스킬도 자동으로 읽을 수는 없다.

## frontmatter와 권한

Studio는 평평한 key와 들여쓴 scalar를 읽는다. 여러 줄 description은 `>`·`|`·`>-`·`|-`로
작성하고 중간 빈 줄을 피한다. 중첩 metadata는 실행 설정이 아니다.
`compatibility`·`allowed-tools`는 도구 제공·권한 설정이나 모델에게 전달되는 본문이 아니다.
필수 도구 조건과 대안은 description·본문에 적는다. description에는 1024 UTF-16 code unit
제한도 적용된다. 저장소 검사기는 이 배포 정책을 규격 검사와 함께 확인한다.
