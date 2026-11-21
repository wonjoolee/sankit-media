# 쓰레드(Threads) 연동 — 대표님이 하실 일

파이프라인은 다 붙여 놨습니다. 아래 8단계만 하시면 됩니다.

> **인스타와 다른 점**: 쓰레드는 인스타처럼 앱 화면에 '토큰 생성' 버튼이 없습니다.
> 브라우저로 한 번 승인하고 거기서 나온 `code` 를 토큰으로 바꿔야 합니다.
> 그 두 단계를 `pipeline/threads_token.py` 가 대신합니다.

## 1. 쓰레드 계정 만들기

threads.com 또는 인스타 앱에서 **@sankitmag 인스타 계정으로** 쓰레드 계정을 만듭니다.
아이디가 그대로 쓰입니다.

## 2. Meta 앱에 Threads 추가

developers.facebook.com → **내 앱**

- 기존 인스타 앱에 추가: **사용 사례(Use cases) → 사용 사례 추가 → Threads API**
- 없으면 **앱 만들기** 에서 **Threads** 사용 사례를 고릅니다.

> 앱에 ID·시크릿이 두 쌍 생깁니다. 반드시 **Threads 앱 ID / Threads 앱 시크릿** 을 씁니다.
> 위치: **앱 설정 → 기본 설정**

## 3. 리디렉션 URI 등록

**Threads API → 설정** 의 **리디렉션 콜백 URL** 에 아래를 넣고 저장합니다.

```
https://github.com/wonjoolee/sankit-media
```

실제로 쓰이는 페이지가 아닙니다. 승인이 끝나면 이 주소로 돌아오는데,
그때 **주소창에 붙는 `code=...`** 만 필요합니다.

## 4. 본인을 Threads 테스터로 등록

1. 앱 대시보드 → **앱 역할(App roles) → 역할(Roles)**
2. **사람 추가(Add People)**
3. **Threads 테스터(Threads Tester)** 선택 후 @sankitmag 초대

## 5. 초대 수락

threads.com → **계정 설정 → 웹사이트 권한 → 초대(Invites) 탭 → 수락**

> **이 단계를 거치면 앱 심사 없이 본인 계정에 발행할 수 있습니다.** 심사 신청 안 해도 됩니다.

## 6. 승인 주소 만들기

```
python3 pipeline/threads_token.py url <Threads앱ID> https://github.com/wonjoolee/sankit-media
```

나온 주소를 브라우저에 붙여 넣고 승인합니다.
승인이 끝나면 주소창이 `...sankit-media?code=XXXXX#_` 로 바뀝니다. **그 주소를 통째로 복사합니다.**

## 7. 토큰 받기

```
python3 pipeline/threads_token.py token <Threads앱ID> <Threads앱시크릿> https://github.com/wonjoolee/sankit-media "<복사한 주소>"
```

`TH_USER_ID` 와 60일짜리 `TH_TOKEN` 이 나옵니다.

## 8. GitHub 시크릿에 넣기

`github.com/wonjoolee/sankit-media` → **Settings → Secrets and variables → Actions → New repository secret**

| 이름 | 값 |
|---|---|
| `TH_TOKEN` | 7단계에서 나온 토큰 |
| `TH_USER_ID` | 7단계에서 나온 사용자 ID |

---

## 끝. 이후는 자동

- `queue/YYYY-MM-DD/slotN/threads.json` 이 있는 슬롯만 쓰레드에 올라갑니다.
- 인스타 발행과 같은 워크플로에서 이어서 돕니다. 토큰이 없으면 조용히 건너뜁니다.
- 발행되면 같은 폴더에 `threads_posted.json` 이 생겨 중복 발행을 막습니다.

확인:
```
TH_TOKEN=... python3 pipeline/threads.py whoami
```

## 60일마다 갱신

```
python3 pipeline/threads_token.py refresh <현재 토큰>
```
만료 전에 해야 합니다. 60일 넘기면 6~7단계를 다시 해야 합니다.
**토큰 갱신 알림은 제가 챙기겠습니다.**

## 지금 준비된 글

| 슬롯 | 내용 | 글자 수 |
|---|---|---|
| 2026-11-21 slot2 | 하이원 11.24 개장, 종일권 2,000원 | 168/500 |
| 2026-11-21 slot3 | 한라산 겨울 입산 마감 11:30 | 190/500 |

## 2주 뒤 점검

인스타와 비교해 **팔로워가 어느 쪽에서 더 늘었는지**만 봅니다. 안 되면 접습니다.
