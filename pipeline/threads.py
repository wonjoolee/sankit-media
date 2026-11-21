"""쓰레드(Threads) 발행.

queue/YYYY-MM-DD/slotN/threads.json 이 있으면 그 내용을 @sankitmag 쓰레드에 올린다.
인스타 캐러셀을 그대로 복사하지 않는다. 쓰레드는 별도의 짧은 글이다(EDITORIAL §23).

threads.json 형식
  {"text": "세 줄 이내 글 + 질문 하나", "image": "01.jpg"}      사진 1장
  {"text": "..."}                                              글만
  {"text": "...", "images": ["01.jpg", "03.jpg"]}              캐러셀(2~20장)

환경변수
  TH_TOKEN     쓰레드 액세스 토큰 (필수)
  TH_USER_ID   쓰레드 사용자 ID (없으면 /me 로 조회)
  DRY_RUN=1    실제로 올리지 않고 점검만

사용
  python3 pipeline/threads.py whoami                 토큰 확인 + 사용자 ID 출력
  python3 pipeline/threads.py queue/2026-11-21/slot1 해당 슬롯 발행
  python3 pipeline/threads.py                        지금 시각 기준 가장 최근 슬롯 발행
"""
import json, os, re, sys, time, datetime, urllib.request, urllib.parse, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = datetime.timezone(datetime.timedelta(hours=9))
REPO = os.environ.get("GITHUB_REPOSITORY", "wonjoolee/sankit-media")
RAW = f"https://raw.githubusercontent.com/{REPO}/main/"
DRY = os.environ.get("DRY_RUN") == "1"
T = os.environ.get("TH_TOKEN", "")
B = "https://graph.threads.com/v1.0"
LIMIT = 500          # 쓰레드 글자 수 상한
WAIT = 30            # 컨테이너 생성 후 대기(초). 공식 문서 권장값.


def call(method, path, params):
    params = dict(params, access_token=T)
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(B + path + "?" + data.decode())
    else:
        req = urllib.request.Request(B + path, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return {"error": json.load(e).get("error")}
        except Exception:
            return {"error": str(e)}


def me():
    r = call("GET", "/me", {"fields": "id,username"})
    if "error" in r:
        raise SystemExit(f"쓰레드 토큰 확인 실패: {r['error']}")
    return r


def user_id():
    u = os.environ.get("TH_USER_ID")
    return u if u else me()["id"]


def length(s):
    """쓰레드 글자 수. 일반 문자는 1자, 이모지는 UTF-8 바이트 길이로 센다(공식 문서).

    한글·한자는 UTF-8로 3바이트지만 1자로 센다. 이모지만 바이트로 센다.
    ⛷️ 처럼 BMP 안에 있는 이모지도 있으므로 코드포인트 크기가 아니라 문자 분류로 판단한다."""
    import unicodedata
    n = 0
    for c in s:
        o = ord(c)
        emoji = (unicodedata.category(c) == "So"          # 기타 기호(대부분의 이모지)
                 or o in (0xFE0F, 0xFE0E, 0x200D)         # 변이 선택자, ZWJ
                 or 0x1F000 <= o <= 0x1FAFF
                 or 0x1F3FB <= o <= 0x1F3FF)              # 피부색 수정자
        n += len(c.encode("utf-8")) if emoji else 1
    return n


def container(uid, p):
    r = call("POST", f"/{uid}/threads", p)
    if "error" in r:
        raise SystemExit(f"컨테이너 생성 실패: {r['error']}")
    return r["id"]


def publish(uid, cid):
    r = call("POST", f"/{uid}/threads_publish", {"creation_id": cid})
    if "error" in r:
        raise SystemExit(f"발행 실패: {r['error']}")
    return r["id"]


def permalink(mid):
    r = call("GET", f"/{mid}", {"fields": "permalink"})
    return r.get("permalink", "")


def post_slot(rel):
    d = os.path.join(ROOT, rel)
    f = os.path.join(d, "threads.json")
    if not os.path.exists(f):
        print("threads.json 없음 — 건너뜀:", rel)
        return None
    done = os.path.join(d, "threads_posted.json")
    if os.path.exists(done):
        print("이미 발행됨:", rel)
        return None

    t = json.load(open(f, encoding="utf-8"))
    text = (t.get("text") or "").strip()
    if not text:
        raise SystemExit("threads.json 에 text 가 비어 있음")
    n = length(text)
    if n > LIMIT:
        raise SystemExit(f"글자 수 초과: {n}/{LIMIT}. 줄여서 다시 쓸 것(요약 자르기 금지).")

    imgs = t.get("images") or ([t["image"]] if t.get("image") else [])
    for i in imgs:
        if not os.path.exists(os.path.join(d, i)):
            raise SystemExit(f"이미지 없음: {rel}/{i}")
    if len(imgs) > 20:
        raise SystemExit(f"캐러셀 상한 20장 초과: {len(imgs)}장")

    if DRY:
        print(f"DRY RUN: {n}/{LIMIT}자, 이미지 {len(imgs)}장")
        print(text)
        return None
    if not T:
        raise SystemExit("TH_TOKEN 없음")

    uid = user_id()
    if not imgs:
        cid = container(uid, {"media_type": "TEXT", "text": text})
    elif len(imgs) == 1:
        cid = container(uid, {"media_type": "IMAGE", "image_url": RAW + rel + "/" + imgs[0], "text": text})
    else:
        kids = []
        for i in imgs:
            kids.append(container(uid, {"media_type": "IMAGE", "image_url": RAW + rel + "/" + i,
                                        "is_carousel_item": "true"}))
            time.sleep(3)
        time.sleep(WAIT)
        cid = container(uid, {"media_type": "CAROUSEL", "children": ",".join(kids), "text": text})

    time.sleep(WAIT)
    mid = publish(uid, cid)
    out = {"id": mid, "url": permalink(mid), "chars": n, "images": len(imgs),
           "posted_at": datetime.datetime.now(KST).isoformat()}
    json.dump(out, open(done, "w"), ensure_ascii=False, indent=1)
    print("쓰레드 발행:", out["url"] or mid)
    return out


def latest_slot():
    """오늘 날짜 폴더에서 threads.json 이 있고 아직 안 올라간 가장 이른 슬롯."""
    now = datetime.datetime.now(KST)
    day = os.path.join(ROOT, "queue", f"{now:%Y-%m-%d}")
    if not os.path.isdir(day):
        return None
    for s in sorted(os.listdir(day)):
        d = os.path.join(day, s)
        if os.path.exists(os.path.join(d, "threads.json")) and not os.path.exists(os.path.join(d, "threads_posted.json")):
            return f"queue/{now:%Y-%m-%d}/{s}"
    return None


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else ""
    if a == "whoami":
        print(json.dumps(me(), ensure_ascii=False))
    else:
        rel = a.strip("/") if a else latest_slot()
        if not rel:
            print("올릴 쓰레드 글 없음")
        else:
            post_slot(rel)
