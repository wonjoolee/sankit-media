"""팔로워 수를 하루 한 번 pipeline/followers.csv 에 남긴다(날짜, 팔로워, 팔로잉, 게시물 수, 전날 대비).
성장 단계의 핵심 지표. 인사이트 권한 없이도 된다. 오늘 줄이 이미 있으면 API를 부르지 않는다."""
import csv, datetime, json, os, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T, U = os.environ.get("IG_TOKEN", ""), os.environ.get("IG_USER_ID", "")
P = os.path.join(ROOT, "pipeline", "followers.csv")
today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d")
rows = list(csv.reader(open(P, encoding="utf-8"))) if os.path.exists(P) else [["date", "followers", "following", "posts", "change"]]
if not (T and U) or any(r and r[0] == today for r in rows[1:]):
    raise SystemExit(0)
q = urllib.parse.urlencode({"fields": "followers_count,follows_count,media_count", "access_token": T})
try:
    d = json.load(urllib.request.urlopen(f"https://graph.facebook.com/v21.0/{U}?{q}", timeout=30))
except Exception as e:
    print("followers: skip", str(e)[:80]); raise SystemExit(0)
prev = int(rows[-1][1]) if len(rows) > 1 and rows[-1][1].isdigit() else None
f = d.get("followers_count", 0)
rows.append([today, f, d.get("follows_count", ""), d.get("media_count", ""), "" if prev is None else f - prev])
csv.writer(open(P, "w", newline="", encoding="utf-8")).writerows(rows)
print("followers:", today, f)
