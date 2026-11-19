# 마무트 Prezly 뉴스룸 — 사용 보류 (2026-11-20 확인)

주소: https://pr.mammut.com/media  (쉘에서 열림, 사진 CDN `cdn.uc.assets.prezly.com` 도 열림)

## 구조
- 앨범 6개. HTML 안에 JSON으로 `download_url`이 그대로 들어 있어 **렌더링이 필요 없다.**
  `"download_url":"https://cdn.uc.assets.prezly.com/<uuid>/-/inline/no/<파일명>"`
- 확인된 `download_url` **335개**.
- 산킷에 맞는 앨범:
  - FREERIDE Images Fall/Winter 2025
  - EIGER EXTREME Nordwand 6.0 Images Fall/Winter 2025
  - Hiking Patrol + Mammut (Product / Mood)
- 앨범 주소 형태: `https://pr.mammut.com/media/album/<uuid>`

## 왜 아직 받지 않았는가
**라이선스·사용조건 표기가 뉴스룸 어디에도 없다.** 약관 링크는 Prezly의 개인정보 요청 페이지 하나뿐이다.
애토믹(Mynewsdesk)은 사진마다 `License: Media Use` 와 조건 원문을 명시하지만, 마무트는 아니다.

→ EDITORIAL 21절 3항에 따라 **내려받지 않고 쓰지 않는다.** `assets/press/` 에 넣지 않는다.
→ 'Download 버튼이 있으니 써도 된다'고 보지 않는다. 버튼은 조건이 아니다.

## 열기 위해 할 일
자료 요청 메일에 **사진 사용 조건을 글로 달라**는 항목을 넣어 보낸다. 받을 곳은 두 곳이다.
- `mammut@crystal-communications.de` (crystal communications GmbH, 마무트 PR 대행, +49 89 6146 5225)
- `pr@mammut.com` (스위스 Seon 본사)

요청 문구에 넣을 것: 뉴스룸 사진을 산킷 인스타그램 카드에 쓸 수 있는지, 크레딧 표기 형식,
수정(자르기·글자 얹기)이 가능한지. 수정 불가라면 애토믹과 같은 규칙(21절)으로 다루면 된다.

서면 답을 받으면 `pipeline/fetch_presskit.py` 에 Prezly 모드를 붙인다. JSON에서 바로 뽑으면 되므로
Mynewsdesk 쪽보다 간단하다. 지금 만들어 두지 않는 이유는 **쓸 수 없는 것을 쌓지 않기 위해서다.**
