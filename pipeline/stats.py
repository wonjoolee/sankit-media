"""최근 게시물 반응(좋아요·댓글)을 queue/*/posted.json 과 묶어 pipeline/stats.csv 로 저장.
GitHub Actions 게시 실행 끝에 돈다. 환경변수 IG_TOKEN, IG_USER_ID."""
import csv, glob, json, os, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T, U = os.environ.get("IG_TOKEN", ""), os.environ.get("IG_USER_ID", "")
if not (T and U):
    raise SystemExit(0)
q = urllib.parse.urlencode({"fields": "id,like_count,comments_count", "limit": 100, "access_token": T})
with urllib.request.urlopen(f"https://graph.facebook.com/v21.0/{U}/media?{q}", timeout=60) as r:
    m = {x["id"]: x for x in json.load(r).get("data", [])}
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
        rows.append([day, slot, kind, cap[0][:40], post.get("type", ""), post.get("hook", ""),
                     x.get("like_count", ""), x.get("comments_count", ""), po.get("posted_at", "")[11:16]])
with open(os.path.join(ROOT, "pipeline", "stats.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["date", "slot", "kind", "title", "type", "hook", "likes", "comments", "posted_at"]); w.writerows(rows)
print("stats rows", len(rows))
