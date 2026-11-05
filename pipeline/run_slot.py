"""GitHub Actions에서 실행: 현재 KST 시간대의 queue 게시물을 인스타그램에 게시.

queue/YYYY-MM-DD/slotN/
  post.json   {"caption": "...", "tags": [{"username":"head_ski","x":0.5,"y":0.4}], "reel_caption": "..."}
  01.jpg..05.jpg   카드 (1080x1350)
  reel.mp4         릴스 (1080x1920, 선택)
  posted.json      게시 후 자동 생성 (중복 게시 방지)

환경변수: IG_TOKEN, IG_USER_ID, GITHUB_REPOSITORY, DRY_RUN(선택), SLOT(선택: 1/2/3 강제)
queue/PAUSE 파일이 있으면 아무것도 게시하지 않음.
"""
import json, os, re, sys, time, datetime, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = datetime.timezone(datetime.timedelta(hours=9))
now = datetime.datetime.now(KST)
REPO = os.environ.get("GITHUB_REPOSITORY", "wonjoolee/sankit-media")
RAW = f"https://raw.githubusercontent.com/{REPO}/main/"
DRY = os.environ.get("DRY_RUN") == "1"
T = os.environ.get("IG_TOKEN", "")
U = os.environ.get("IG_USER_ID", "")
B = "https://graph.facebook.com/v21.0"


SLOT_TIMES = {"1": "07:30", "4": "10:00", "2": "12:10", "5": "18:00", "3": "21:00"}  # 슬롯별 게시 시각(KST)


def slot_now():
    """수동 실행이면 SLOT 값. 예약 실행이면 '오늘 시각이 지났는데 아직 안 올라간' 가장 이른 슬롯 하나."""
    if os.environ.get("SLOT"):
        return int(os.environ["SLOT"])
    hm = now.strftime("%H:%M")
    day = os.path.join(ROOT, "queue", f"{now:%Y-%m-%d}")
    for sl, t in sorted(SLOT_TIMES.items(), key=lambda kv: kv[1]):
        if t > hm:
            break
        d = os.path.join(day, f"slot{sl}")
        if os.path.exists(os.path.join(d, "post.json")) and not os.path.exists(os.path.join(d, "posted.json")):
            return int(sl)
    return 0


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


def wait(cid, tries=60, gap=5):
    s = {}
    for _ in range(tries):
        s = call("GET", "/" + cid, {"fields": "status_code,status"})
        if s.get("status_code") in ("FINISHED", "ERROR", "EXPIRED"):
            return s
        time.sleep(gap)
    return s


def permalink(mid):
    return call("GET", "/" + mid, {"fields": "permalink"}).get("permalink")


def single_image(rel, post, f):
    """카드가 1장이면 캐러셀 대신 단일 이미지로 게시."""
    p = {"image_url": RAW + rel + "/" + f, "caption": post["caption"]}
    if post.get("tags"):
        p["user_tags"] = json.dumps(post["tags"])
    r = call("POST", f"/{U}/media", p)
    if "error" in r and "user_tags" in p:
        p.pop("user_tags"); r = call("POST", f"/{U}/media", p)
    if "error" in r:
        raise SystemExit(f"image error: {r}")
    s = wait(r["id"], 30, 3)
    if s.get("status_code") != "FINISHED":
        raise SystemExit(f"image not finished: {s}")
    pb = call("POST", f"/{U}/media_publish", {"creation_id": r["id"]})
    if "error" in pb:
        raise SystemExit(f"publish error: {pb}")
    return pb["id"], permalink(pb["id"])


def carousel(rel, post):
    imgs = sorted(f for f in os.listdir(os.path.join(ROOT, rel)) if re.fullmatch(r"\d\d\.jpg", f))[:10]
    if len(imgs) == 1:
        return single_image(rel, post, imgs[0])
    kids = []
    for i, f in enumerate(imgs):
        p = {"image_url": RAW + rel + "/" + f, "is_carousel_item": "true"}
        if i == 0 and post.get("tags"):
            p["user_tags"] = json.dumps(post["tags"])
        r = call("POST", f"/{U}/media", p)
        if "error" in r and "user_tags" in p:
            print("tag failed, retry without tag:", r["error"])
            p.pop("user_tags")
            r = call("POST", f"/{U}/media", p)
        if "error" in r:
            raise SystemExit(f"child error {f}: {r}")
        s = wait(r["id"], 30, 3)
        if s.get("status_code") != "FINISHED":
            raise SystemExit(f"child not finished {f}: {s}")
        kids.append(r["id"])
    r = call("POST", f"/{U}/media", {"media_type": "CAROUSEL", "children": ",".join(kids), "caption": post["caption"]})
    if "error" in r:
        raise SystemExit(f"carousel error: {r}")
    s = wait(r["id"], 30, 3)
    if s.get("status_code") != "FINISHED":
        raise SystemExit(f"carousel not finished: {s}")
    p = call("POST", f"/{U}/media_publish", {"creation_id": r["id"]})
    if "error" in p:
        raise SystemExit(f"publish error: {p}")
    return p["id"], permalink(p["id"])


def reel(rel, post):
    r = call("POST", f"/{U}/media", {"media_type": "REELS", "video_url": RAW + rel + "/reel.mp4",
                                     "caption": post.get("reel_caption") or post["caption"], "share_to_feed": "true"})
    if "error" in r:
        raise SystemExit(f"reel error: {r}")
    s = wait(r["id"])
    if s.get("status_code") != "FINISHED":
        raise SystemExit(f"reel not finished: {s}")
    p = call("POST", f"/{U}/media_publish", {"creation_id": r["id"]})
    if "error" in p:
        raise SystemExit(f"reel publish error: {p}")
    return p["id"], permalink(p["id"])


def story(rel):
    """스토리 게시: story.jpg(1080x1920) > reel.mp4 > 01.jpg 순서로 있는 것을 쓴다. 캡션·링크는 붙지 않는다."""
    d = os.path.join(ROOT, rel)
    if os.path.exists(os.path.join(d, "story.jpg")):
        params = {"media_type": "STORIES", "image_url": RAW + rel + "/story.jpg"}
    elif os.path.exists(os.path.join(d, "reel.mp4")):
        params = {"media_type": "STORIES", "video_url": RAW + rel + "/reel.mp4"}
    else:
        params = {"media_type": "STORIES", "image_url": RAW + rel + "/01.jpg"}
    r = call("POST", f"/{U}/media", params)
    if "error" in r:
        raise SystemExit(f"story error: {r}")
    s = wait(r["id"])
    if s.get("status_code") != "FINISHED":
        raise SystemExit(f"story not finished: {s}")
    p = call("POST", f"/{U}/media_publish", {"creation_id": r["id"]})
    if "error" in p:
        raise SystemExit(f"story publish error: {p}")
    return p["id"]


def main():
    if os.path.exists(os.path.join(ROOT, "queue", "PAUSE")):
        print("PAUSED: queue/PAUSE exists")
        return
    slot = slot_now()
    if slot == 0:
        print("KST", now.isoformat(), "nothing due")
        return
    rel = f"queue/{now:%Y-%m-%d}/slot{slot}"
    d = os.path.join(ROOT, rel)
    print("KST", now.isoformat(), "slot", slot, rel)
    if not os.path.isdir(d) or not os.path.exists(os.path.join(d, "post.json")):
        print("nothing queued")
        return
    if os.path.exists(os.path.join(d, "posted.json")):
        print("already posted")
        return
    post = json.load(open(os.path.join(d, "post.json"), encoding="utf-8"))
    if DRY:
        imgs = [f for f in os.listdir(d) if f.endswith(".jpg")]
        print("DRY RUN ok:", len(imgs), "cards, reel:", os.path.exists(os.path.join(d, "reel.mp4")))
        print(post["caption"][:200])
        return
    if not (T and U):
        raise SystemExit("IG_TOKEN / IG_USER_ID secrets missing")
    out = {"slot": slot, "posted_at": datetime.datetime.now(KST).isoformat()}
    out["carousel_id"], out["carousel_url"] = carousel(rel, post)
    print("carousel:", out["carousel_url"])
    if os.path.exists(os.path.join(d, "reel.mp4")):
        try:
            out["reel_id"], out["reel_url"] = reel(rel, post)
            print("reel:", out["reel_url"])
        except SystemExit as e:
            out["reel_error"] = str(e)
            print("reel failed:", e)
    if os.environ.get("NO_STORY") != "1":
        try:
            out["story_id"] = story(rel)
            print("story:", out["story_id"])
        except SystemExit as e:
            out["story_error"] = str(e)
            print("story failed:", e)
    json.dump(out, open(os.path.join(d, "posted.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
