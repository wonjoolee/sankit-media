"""오늘(KST) 아직 게시 전인 슬롯 중 reel.mp4가 없는 것에 릴스를 자동으로 만든다.

2026-11-27 운영자 지시: 모든 글이 피드·스토리·릴스·쓰레드에 각각의 형태로 올라가야 한다.
지난 1주 릴스가 21개 중 8개뿐이었다(글자 카드 글은 릴스를 만들지 않았기 때문).

사진 고르기
  1) 슬롯 폴더의 사진(01~06.jpg·story.jpg 제외, 예: cover.jpg)과 kit.html이 불러오는 저장소 사진(assets/…)
     → 사진 중심 릴스(reel.py). 프레스 사진(assets/press)이 하나라도 있으면 'press' 모드(자르기 없음).
  2) 사진이 하나도 없으면 표지 카드(01.jpg)를 통째로 천천히 보여 주는 릴스(자르지 않음, 카드 넘기기 아님).
건너뛰기: post.json에 "no_reel": true, 이미 posted.json이 있는 슬롯.
출력 마지막 줄: 'created N'.
"""
import datetime, glob, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = datetime.timezone(datetime.timedelta(hours=9))
day = sys.argv[1] if len(sys.argv) > 1 else datetime.datetime.now(KST).strftime("%Y-%m-%d")
CARD = re.compile(r"^(0\d|story)\.jpe?g$", re.I)


def photos(d):
    found = []
    for f in sorted(os.listdir(d)):
        if f.lower().endswith((".jpg", ".jpeg", ".png")) and not CARD.match(f):
            found.append(os.path.join(d, f))
    kh = os.path.join(d, "kit.html")
    if os.path.exists(kh):
        for src in re.findall(r'<img[^>]+src="([^"]+)"', open(kh, encoding="utf-8").read()):
            if src.startswith(("http", "data:")):
                continue
            p = os.path.normpath(os.path.join(d, src))
            if os.path.exists(p) and p not in found and not CARD.match(os.path.basename(p)):
                found.append(p)
    out = []
    try:
        from PIL import Image
        for p in found:
            w, h = Image.open(p).size
            if min(w, h) >= 600:
                out.append(p)
    except Exception:
        out = found
    return out[:4]


def title_of(post):
    first = post.get("caption", "").split("\n")[0]
    m = re.search(r"KIT\s*0*(\d+)", post.get("caption", ""))
    kit = f"KIT {int(m.group(1)):03d}" if m else "SANKIT"
    t = re.sub(r"\s*\(KIT\s*\d+\)\s*", "", first).strip()
    return kit, t


def wrap(t, n=13):
    words, lines, cur = t.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines[:3]


made = 0
for d in sorted(glob.glob(os.path.join(ROOT, "queue", day, "slot*"))):
    pj = os.path.join(d, "post.json")
    if not os.path.exists(pj) or os.path.exists(os.path.join(d, "posted.json")) or os.path.exists(os.path.join(d, "reel.mp4")):
        continue
    post = json.load(open(pj, encoding="utf-8"))
    if post.get("no_reel"):
        continue
    kit, title = title_of(post)
    ph = photos(d)
    if ph:
        mode = "press" if any("/assets/press/" in p for p in ph) else "own"
        scenes = []
        for i, p in enumerate(ph):
            s = {"img": p, "sec": 5.5}
            if i == 0:
                s.update(kick=f"SANKIT · {kit}", lines=wrap(title))
            else:
                s.update(kick="", lines=[])
            scenes.append(s)
        credit = "PHOTO · SANKIT  ·  @SANKITMAG" if mode == "own" else "PHOTO · " + (post.get("credit") or "보도용 사진") + "  ·  @SANKITMAG"
    else:
        card = os.path.join(d, "01.jpg")
        if not os.path.exists(card):
            continue
        mode = "press"  # 카드를 자르지 않고 통째로, 아주 천천히
        scenes = [{"img": card, "sec": 7.0, "kick": "", "lines": []}]
        credit = "@SANKITMAG"
    cfg = {"mode": mode, "credit": credit, "scenes": scenes}
    cp = os.path.join(d, "reel_auto.json")
    json.dump(cfg, open(cp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "pipeline", "reel.py"), cp, os.path.join(d, "reel.mp4")])
    if r.returncode != 0 or not os.path.exists(os.path.join(d, "reel.mp4")):
        print("reel failed", d)
        continue
    if not post.get("reel_caption"):
        tags = " ".join(re.findall(r"#\S+", post.get("caption", ""))[:6])
        post["reel_caption"] = f"{title}\n\n자세한 이야기는 피드의 {kit}에서.\n\n{tags}".strip()
        json.dump(post, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    made += 1
    print("reel", d, mode, len(scenes), "scene(s)")
print("created", made)
