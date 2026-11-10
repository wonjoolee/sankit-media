"""산악 안전 알림: 산악예보(data/latest/mountain_weather.json)와 기상특보(data/latest/warnings.json, 있으면)를 보고
오늘·내일 정상부에 위험 신호가 있으면 9:16 스토리 이미지를 만든다. 하루 한 번만.

기준(정상부 예보)
- 최저기온 -10℃ 이하
- 최대 풍속 10m/s 이상
- 눈 예보(적설 표시가 있을 때)

출력: queue/alerts/<YYYY-MM-DD>/story.jpg, alert.json  → 마지막 줄 'ALERT queue/alerts/<날짜>' 또는 'NO ALERT'
게시는 workflow에서 run_slot.py(STORY_ONLY)로 한다. 이미 만든 날짜는 다시 만들지 않는다.
"""
import datetime, json, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = datetime.timezone(datetime.timedelta(hours=9))
now = datetime.datetime.now(KST)
FONTS = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"]
WD = "월화수목금토일"


def font(size, bold=True):
    for f in FONTS if bold else FONTS[::-1]:
        if os.path.exists(f):
            return ImageFont.truetype(f, size, index=1)  # 1 = KR
    raise SystemExit("Korean font missing (apt-get install fonts-noto-cjk)")


def load(p):
    try:
        return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))["data"]
    except Exception:
        return None


def findings():
    mw = load("data/latest/mountain_weather.json")
    out = []
    if not mw:
        return out, None
    # 오래된 예보로 알림을 내지 않는다: 발표 시각(base)이 12시간 넘게 지났으면 무시
    try:
        b = datetime.datetime.strptime(mw["base"], "%Y%m%d%H%M").replace(tzinfo=KST)
        if now - b > datetime.timedelta(hours=12):
            print("mountain forecast is stale:", mw["base"], "- no alert from it (KMA_KEY secret missing?)")
            return out, None
    except Exception:
        return out, None
    days = [(now + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in (0, 1)]
    if now.hour >= 15:  # 오후에는 오늘보다 내일이 중요
        days = days[1:]
    for m in mw["mountains"]:
        for day in days:
            x = m["days"].get(day)
            if not x:
                continue
            why = []
            if x.get("tmin", 99) <= -10:
                why.append(f"{x['tmin']:g}℃")
            if x.get("wsd_max", 0) >= 10:
                why.append(f"바람 {x['wsd_max']:g}m/s")
            sno = x.get("sno", "")
            if sno and "없음" not in sno:
                why.append(f"눈 {sno}")
            if why:
                score = (x.get("wsd_max", 0) >= 10) * 2 + (x.get("tmin", 0) <= -10) * 2 + bool(sno and "없음" not in sno) * 3
                out.append({"day": day, "name": m["name"], "alt": m["alt"], "why": why, "score": score,
                            "tmin": x.get("tmin"), "wsd": x.get("wsd_max")})
    out.sort(key=lambda r: (r["day"], -r["score"], r.get("tmin") or 0))
    return out, mw.get("base")


def warnings():
    w = load("data/latest/warnings.json")
    return (w or {}).get("items", [])


def draw(rows, warns, base, path):
    W, H = 1080, 1920
    im = Image.new("RGB", (W, H), (20, 22, 21))
    d = ImageDraw.Draw(im)
    gold, ink, mute = (217, 164, 65), (244, 242, 236), (150, 155, 152)
    d.text((80, 300), "SANKIT  산악 안전 알림", font=font(36), fill=gold)
    day = rows[0]["day"] if rows else now.strftime("%Y%m%d")
    dt = datetime.datetime.strptime(day, "%Y%m%d")
    when = "오늘" if day == now.strftime("%Y%m%d") else "내일"
    d.text((80, 360), f"{when} {dt.month}.{dt.day}({WD[dt.weekday()]}) 정상부 예보", font=font(34, False), fill=mute)
    top = rows[0] if rows else None
    head = []
    if warns:
        head = [warns[0]["title"][:14], "발효 중"]
    elif top:
        kind = "눈 예보" if any(w.startswith("눈") for w in top["why"]) else ("강풍" if any("바람" in w for w in top["why"]) else "한파")
        head = [f"{top['name']} 정상", kind]
    y = 450
    for line in head:
        d.text((80, y), line, font=font(104), fill=ink); y += 130
    y += 50
    d.line((80, y, W - 80, y), fill=(60, 63, 61), width=3); y += 40
    shown = set()
    for r in rows:
        if r["name"] in shown or len(shown) >= 5:
            continue
        shown.add(r["name"])
        d.text((80, y), r["name"], font=font(54), fill=ink)
        d.text((80 + d.textlength(r["name"], font=font(54)) + 18, y + 18), f"{r['alt']}m".replace("mm", "m"), font=font(28, False), fill=mute)
        t = " · ".join(r["why"])
        d.text((W - 80 - d.textlength(t, font=font(44)), y + 6), t, font=font(44), fill=gold)
        y += 100
    for wv in warns[1:4]:
        d.text((80, y), wv["title"][:30], font=font(40, False), fill=ink); y += 70
    y = max(y + 40, 1440)
    for t in ["모자·장갑·보온층, 하산 시간 여유 있게.", "출발 전 날씨누리·국립공원 통제 정보 확인."]:
        d.text((80, y), t, font=font(38, False), fill=ink); y += 62
    src = "기상청 산악예보" + (f" {base[8:10]}:{base[10:12]} 발표" if base else "") + (" · 기상특보" if warns else "")
    d.text((80, 1640), src, font=font(28, False), fill=mute)
    d.text((80, 1690), "@sankitmag", font=font(30), fill=gold)
    im.save(path, quality=92)


def main():
    rel = f"queue/alerts/{now:%Y-%m-%d}"
    d = os.path.join(ROOT, rel)
    if os.path.exists(os.path.join(d, "alert.json")):
        if os.path.exists(os.path.join(d, "posted")):
            print("already posted today"); print("NO ALERT")
        else:
            print(f"ALERT {rel}")  # 만들었지만 아직 못 올림(심야 등) → 다시 게시 시도
        return
    rows, base = findings()
    warns = warnings()
    if not rows and not warns:
        print("NO ALERT"); return
    os.makedirs(d, exist_ok=True)
    draw(rows, warns, base, os.path.join(d, "story.jpg"))
    json.dump({"made_at": now.isoformat(), "base": base, "rows": rows[:10], "warnings": warns[:5]},
              open(os.path.join(d, "alert.json"), "w"), ensure_ascii=False, indent=1)
    print(f"ALERT {rel}")


if __name__ == "__main__":
    main()
