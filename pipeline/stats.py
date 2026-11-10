"""최근 게시물 반응(좋아요·댓글)을 queue/*/posted.json 과 묶어 pipeline/stats.csv 로 저장.
GitHub Actions 게시 실행 끝에 돈다. 환경변수 IG_TOKEN, IG_USER_ID."""
import csv, glob, json, os, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T, U = os.environ.get("IG_TOKEN", ""), os.environ.get("IG_USER_ID", "")
if not (T and U):
    raise SystemExit(0)
import datetime  # every 3h: 호출 수 절약(앱 호출 한도)
_n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
if not os.environ.get("FORCE_STATS") and not (_n.hour % 3 == 0 and _n.minute < 15):
    raise SystemExit(0)
q = urllib.parse.urlencode({"fields": "id,like_count,comments_count", "limit": 100, "access_token": T})
with urllib.request.urlopen(f"https://graph.facebook.com/v21.0/{U}/media?{q}", timeout=60) as r:
    m = {x["id"]: x for x in json.load(r).get("data", [])}
# 저장·도달·공유: 인사이트 권한(instagram_manage_insights)이 있을 때만. 호출 수를 아끼려고 하루 한 번(09시대), 최근 14일 게시물만.
ins = {}
old = {}
sp = os.path.join(ROOT, "pipeline", "stats.csv")
if os.path.exists(sp):
    for r0 in csv.DictReader(open(sp, encoding="utf-8")):
        old[(r0["date"], r0["slot"], r0["kind"])] = r0
want_ins = os.environ.get("FORCE_STATS") or _n.hour == 9


def insights(mid):
    q2 = urllib.parse.urlencode({"metric": "reach,saved,shares", "access_token": T})
    try:
        with urllib.request.urlopen(f"https://graph.facebook.com/v21.0/{mid}/insights?{q2}", timeout=30) as r2:
            return {x["name"]: x["values"][0]["value"] for x in json.load(r2).get("data", [])}
    except Exception:
        return None
rows = []
for p in sorted(glob.glob(os.path.join(ROOT, "queue", "20*", "slot*", "posted.json"))):
    d = os.path.dirname(p); day = os.path.basename(os.path.dirname(d)); slot = os.path.basename(d)
    po = json.load(open(p)); post = json.load(open(os.path.join(d, "post.json"), encoding="utf-8"))
    cap = post.get("caption", "").split("\n")
    for kind in ("carousel", "reel"):
        mid = po.get(f"{kind}_id")
        if not mid:
            continue
        x = m.get(mid, {})
        prev = old.get((day, slot, kind), {})
        sv, rc, sh = prev.get("saved", ""), prev.get("reach", ""), prev.get("shares", "")
        if want_ins and day >= (_n - datetime.timedelta(days=14)).strftime("%Y-%m-%d"):
            i = insights(mid)
            if i is None:
                want_ins = False  # 권한 없음 → 이번 실행은 더 부르지 않음
            else:
                sv, rc, sh = i.get("saved", ""), i.get("reach", ""), i.get("shares", "")
        rows.append([day, slot, kind, cap[0][:40], post.get("type", ""), post.get("role", ""), post.get("format", ""), post.get("hook", ""),
                     x.get("like_count", ""), x.get("comments_count", ""), sv, rc, sh, po.get("posted_at", "")[11:16]])
with open(os.path.join(ROOT, "pipeline", "stats.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["date", "slot", "kind", "title", "type", "role", "format", "hook", "likes", "comments", "saved", "reach", "shares", "posted_at"]); w.writerows(rows)
print("stats rows", len(rows))
