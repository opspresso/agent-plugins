# Google 문서의 작성과 스타일

Google Docs·Slides가 요청한 결과일 때만 적용한다. DOCX/PPTX Artifact와 Google ID는 다르다.
같은 스킬의 [디자인 계약](design-system.json)을 새 문서의 기준으로 사용하며 실제 tool schema가 우선한다.

## 문서와 양식 선택

1. 실제 Drive·Docs·Slides 도구와 계정 접근을 확인한다. 제목으로 찾을 때는 Drive로 동명 문서를 구분한다.
2. 사용자 템플릿이 있으면 전체 native 파일을 지원되는 copy 도구로 복사하고 새 ID의 구조를 읽는다.
   원본 템플릿과 복사본의 tab·slide·table·master·named style 관계를 유지한다.
3. 생성·copy가 제공되지 않으면 이미 지정한 대상의 요청된 편집만 수행한다. 파일 생성이나 native
   복사 능력을 추측하지 않으며 텍스트나 다운로드 Artifact를 Google 문서로 저장했다고 말하지 않는다.
4. 기존 문구 수정은 주변 서식을 따른다. 새 기본 디자인을 기존 문서 전체에 덮지 않는다.
   새 문서만 사용자 기준이 없을 때 corporate theme와 standard profile을 사용한다.

## Google Docs

read_doc의 실제 구조에서 tab·segment·index와 named style을 얻는다. update_doc가 제공되면
요청한 범위에 해당하는 batch update만 사용한다. 삽입 뒤 index가 움직이는 것을 고려한다.

- 제목·절·본문·캡션을 역할로 구분한다. named style과 text/paragraph style을 함께 확인한다.
- 기본 본문은 `type.page.body` 포인트와 `leading.document.body` 줄 간격을 사용한다.
  문단 간격·정렬과 `page.width`·`page.height`·`page.margin`은 pt 단위에서 실제 DocumentStyle schema로 변환한다.
- compact의 첫 제목은 `type.page.headings[0]`, 바로 아래 문단은 `type.page.body`다.
  report 표지는 `type.page.coverTitle`·`type.page.subtitle` 역할을 사용한다.
  paragraph lineSpacing은 배수를 퍼센트로 바꾼다(1.5 → 150).
- fontFamily는 `fonts.googleBody`의 provider 이름을 사용한다. 현재 문서에 반영된 weightedFontFamily를
  다시 읽고 지원되지 않았거나 대체됐다면 같은 글꼴이라고 주장하지 않는다.
- 색은 6자리 hex를 0–1 RGB로 변환한다. profile의 light/solid 표 머리 처리를 선택한 theme로 적용한다.
- updateTextStyle·updateParagraphStyle·updateTableCellStyle·updateDocumentStyle 등은
  실제 노출 도구의 requests/fields 계약을 사용한다. 관련 없는 스타일 필드를 덮어쓰지 않는다.
- 짧은 compact 문서에는 표지·목차·빈 페이지를 추가하지 않는다. 사용자 양식과 smart chip은 보존한다.

## Google Slides

read_presentation으로 실제 slide/object/master/layout ID와 페이지 크기를 읽는다.
템플릿의 배치와 master를 우선하고 새로운 덱만 계약의 `type.deck`·`leading.deck` 역할을 적용한다.

- 새 덱은 16:9를 기본으로 하고 제목·본문·캡션·표 역할마다 같은 type/색 규칙을 쓴다.
- 계약의 크기는 pt이며 모서리 비율은 `profiles[profile].deck.cornerRadiusFraction`이다. provider에 없는 형태 조정
  속성을 임의로 만들지 않으며 템플릿의 기본 형태를 유지한다.
- updateTextStyle·updateParagraphStyle·updateShapeProperties·updateTableCellProperties와
  transform을 실제 schema로 구성한다. 좌표·크기는 단위를 함께 지정한다.
- 문구 치환 뒤 길이가 늘면 줄바꿈·box 크기·표 밀도를 확인한다. 빈 제목/불필요한 페이지는 만들지 않는다.
- API의 구조 읽기는 실제 렌더링 검사가 아니다. thumbnail·export·preview가 제공되면
  제목 잘림·겹침·폰트 대체·긴 표를 화면에서 확인한다.

## 검증과 전달

변경된 범위의 텍스트·숫자·역할·색·fontFamily·문단 간격을 read로 대조한다. 사용자 지정 양식의
관계와 비대상 요소가 유지됐는지도 확인한다. native 링크와 실제 처리 결과만 전달한다.
export가 없으면 DOCX/PPTX/PDF 다운로드를 약속하지 않는다.

Notion으로 발행하는 별도 요청은 제공된 Notion 도구로 제목·목록·표·강조 역할을 대응시킨다.
Notion의 제한된 색 enum과 블록 구조에는 원래 의미를 유지하며 대응하고 Office의 자유 색·글꼴·여백이
완전히 재현됐다고 말하지 않는다. 외부 게시는 사용자가 허가한 대상과 범위에 한정한다.
