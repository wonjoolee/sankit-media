"""수입사·브랜드 노출 기록: 게시된 글에서 태그한 계정과 본문에 나온 브랜드를 세어 research/exposure.csv 로 남긴다.
12월 미디어킷과 수입사 제안의 근거('산킷이 귀사 브랜드를 N번 다뤘고 저장 M회')로 쓴다. API 호출 없음."""
import csv, glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
brands = list(csv.DictReader(open(os.path.join(ROOT, "research", "brand_map.csv"), encoding="utf-8-sig")))
saved = {}
sp = os.path.join(ROOT, "pipeline", "stats.csv")
if os.path.exists(sp):
    for r in csv.DictReader(open(sp, encoding="utf-8")):
        if r["kind"] == "carousel" and r.get("saved", "").isdigit():
            saved[(r["date"], r["slot"])] = int(r["saved"])

rows = {}
for pj in sorted(glob.glob(os.path.join(ROOT, "queue", "20*", "slot*", "posted.json"))):
    d = os.path.dirname(pj)
    day, slot = d.split(os.sep)[-2:]
    try:
        post = json.load(open(os.path.join(d, "post.json"), encoding="utf-8"))
        po = json.load(open(pj, encoding="utf-8"))
    except Exception:
        continue
    cap = post.get("caption", "")
    tags = {"@" + (t["username"] if isinstance(t, dict) else str(t)).lstrip("@").lower() for t in post.get("tags", []) if t}
    for b in brands:
        name = b["브랜드"].strip()
        insta = b["국내 공식 인스타"].strip().lower()
        hit_tag = insta.startswith("@") and insta in tags
        hit_name = len(name) >= 3 and re.search(r"(?<![A-Za-z])" + re.escape(name) + r"(?![A-Za-z])", cap, re.I)
        if not (hit_tag or hit_name):
            continue
        r = rows.setdefault(name, {"브랜드": name, "국내 수입사·운영사": b["국내 수입사·운영사"], "국내 공식 인스타": b["국내 공식 인스타"],
                                   "다룬 횟수": 0, "태그한 횟수": 0, "저장 합계": 0, "마지막 게시": "", "게시물": []})
        r["다룬 횟수"] += 1
        r["태그한 횟수"] += 1 if hit_tag else 0
        r["저장 합계"] += saved.get((day, slot), 0)
        r["마지막 게시"] = max(r["마지막 게시"], day)
        if po.get("carousel_url"):
            r["게시물"].append(po["carousel_url"])
out = sorted(rows.values(), key=lambda r: (-r["다룬 횟수"], r["브랜드"]))
with open(os.path.join(ROOT, "research", "exposure.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["브랜드", "국내 수입사·운영사", "국내 공식 인스타", "다룬 횟수", "태그한 횟수", "저장 합계", "마지막 게시", "게시물"])
    for r in out:
        w.writerow([r["브랜드"], r["국내 수입사·운영사"], r["국내 공식 인스타"], r["다룬 횟수"], r["태그한 횟수"], r["저장 합계"], r["마지막 게시"], " ".join(r["게시물"][-5:])])
print("exposure:", len(out), "brands")
