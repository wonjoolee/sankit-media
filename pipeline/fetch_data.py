"""공공데이터를 받아 data/ 에 저장한다 (GitHub Actions에서 실행, 키는 secrets).
환경변수: DATA_GO_KR_KEY (공공데이터포털 일반 인증키, Decoding)
산출:
  data/latest/festivals.json   오늘부터 21일 안에 열리는/진행 중인 축제·행사 (한국관광공사)
  data/latest/weather.json     스키장·명산 단기예보 요약 (기상청, 3일)
  data/latest/congestion.json  주요 시군 관광지 혼잡 예측 (한국관광공사, 30일)
  data/reference/*.json        (월요일 또는 없을 때) 두루누비 코스, 고캠핑, 무장애, 100대 명산 산정보
"""
import json, math, os, time, datetime, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.environ.get("DATA_GO_KR_KEY", "")
KST = datetime.timezone(datetime.timedelta(hours=9))
NOW = datetime.datetime.now(KST)
B = "https://apis.data.go.kr"
C = {"MobileOS": "ETC", "MobileApp": "SANKIT", "_type": "json"}

def get(path, params, tries=3):
    q = urllib.parse.urlencode(dict(params, serviceKey=K))
    for i in range(tries):
        try:
            with urllib.request.urlopen(f"{B}{path}?{q}", timeout=40) as r:
                return json.loads(r.read().decode("utf-8", "ignore"))
        except Exception as e:
            err = e; time.sleep(3 * (i + 1))
    print("fail", path, err); return {}

def items(d):
    try:
        body = d["response"]["body"] if "response" in d else d["body"]
        it = body["items"]
        if isinstance(it, list):
            return it
        it = it.get("item", []) if isinstance(it, dict) else []
        return it if isinstance(it, list) else [it]
    except Exception:
        return []

def save(rel, obj):
    p = os.path.join(ROOT, "data", rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump({"fetched_at": NOW.isoformat(), "data": obj}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved", rel, len(obj) if hasattr(obj, "__len__") else "")

# ---- 격자 변환 (기상청 LCC) ----
def grid(lat, lon):
    RE, GRID, SLAT1, SLAT2, OLON, OLAT, XO, YO = 6371.00877, 5.0, 30.0, 60.0, 126.0, 38.0, 43, 136
    D = math.pi / 180.0; re = RE / GRID
    sl1, sl2, ol, oa = SLAT1 * D, SLAT2 * D, OLON * D, OLAT * D
    sn = math.log(math.cos(sl1) / math.cos(sl2)) / math.log(math.tan(math.pi * 0.25 + sl2 * 0.5) / math.tan(math.pi * 0.25 + sl1 * 0.5))
    sf = math.tan(math.pi * 0.25 + sl1 * 0.5) ** sn * math.cos(sl1) / sn
    ro = re * sf / math.tan(math.pi * 0.25 + oa * 0.5) ** sn
    ra = re * sf / math.tan(math.pi * 0.25 + lat * D * 0.5) ** sn
    th = lon * D - ol
    th = th - 2 * math.pi if th > math.pi else th + 2 * math.pi if th < -math.pi else th
    th *= sn
    return int(ra * math.sin(th) + XO + 0.5), int(ro - ra * math.cos(th) + YO + 0.5)

PLACES = [  # 이름, 위도, 경도 (리조트 베이스·산 정상 부근, 대략값)
 ("용평", 37.645, 128.680), ("하이원", 37.208, 128.825), ("휘닉스", 37.582, 128.322), ("비발디파크", 37.646, 127.683),
 ("알펜시아", 37.656, 128.672), ("웰리힐리", 37.486, 128.248), ("무주덕유산", 35.889, 127.737), ("곤지암", 37.337, 127.293),
 ("지산", 37.217, 127.343), ("엘리시안강촌", 37.817, 127.587), ("오크밸리", 37.410, 127.818), ("오투", 37.177, 128.948),
 ("설악산", 38.119, 128.465), ("지리산", 35.337, 127.731), ("한라산", 33.362, 126.533), ("북한산", 37.659, 126.978),
 ("덕유산", 35.860, 127.746), ("속리산", 36.543, 127.870), ("오대산", 37.795, 128.543), ("태백산", 37.095, 128.915),
 ("소백산", 36.957, 128.485), ("민둥산", 37.249, 128.759), ("황령산", 35.157, 129.083)]

def weather():
    base = NOW - datetime.timedelta(hours=3)
    hrs = [2, 5, 8, 11, 14, 17, 20, 23]
    h = max([x for x in hrs if x <= base.hour] or [23])
    if base.hour < 2: base -= datetime.timedelta(days=1)
    bd, bt = base.strftime("%Y%m%d"), f"{h:02d}00"
    out = {}
    for name, la, lo in PLACES:
        nx, ny = grid(la, lo)
        d = get("/1360000/VilageFcstInfoService_2.0/getVilageFcst", {"base_date": bd, "base_time": bt, "nx": nx, "ny": ny, "numOfRows": 1000, "dataType": "JSON"})
        days = {}
        for it in items(d):
            day = days.setdefault(it["fcstDate"], {"TMN": None, "TMX": None, "POP": 0, "SNO": set(), "PTY": set(), "SKY": set()})
            c, v = it["category"], it["fcstValue"]
            if c in ("TMN", "TMX"): day[c] = v
            elif c == "POP": day["POP"] = max(day["POP"], int(v))
            elif c == "SNO" and v not in ("적설없음", "0"): day["SNO"].add(v)
            elif c == "PTY" and v != "0": day["PTY"].add({"1": "비", "2": "비/눈", "3": "눈", "4": "소나기"}.get(v, v))
            elif c == "SKY": day["SKY"].add({"1": "맑음", "3": "구름많음", "4": "흐림"}.get(v, v))
        out[name] = {"grid": [nx, ny], "days": {k: {kk: (sorted(vv) if isinstance(vv, set) else vv) for kk, vv in v.items()} for k, v in sorted(days.items())}}
        time.sleep(0.2)
    save("latest/weather.json", {"base": bd + bt, "places": out})

def festivals():
    start = NOW.strftime("%Y%m%d"); end = (NOW + datetime.timedelta(days=21)).strftime("%Y%m%d")
    allit, page = [], 1
    while page <= 10:
        d = get("/B551011/KorService2/searchFestival2", dict(C, eventStartDate=(NOW - datetime.timedelta(days=60)).strftime("%Y%m%d"), numOfRows=200, pageNo=page, arrange="A"))
        it = items(d)
        if not it: break
        allit += it; page += 1
        if len(it) < 200: break
    keep = [{"title": i.get("title"), "start": i.get("eventstartdate"), "end": i.get("eventenddate"), "addr": i.get("addr1"),
             "areacode": i.get("areacode"), "contentid": i.get("contentid"), "tel": i.get("tel")}
            for i in allit if (i.get("eventenddate") or "0") >= start and (i.get("eventstartdate") or "9") <= end]
    for x in keep:
        try:
            dur = (datetime.datetime.strptime(x["end"], "%Y%m%d") - datetime.datetime.strptime(x["start"], "%Y%m%d")).days + 1
        except Exception:
            dur = None
        x["days"] = dur
        x["short"] = bool(dur and dur <= 31)   # 상시 행사(수개월~1년)는 False — WEEKLY 후보는 short 우선
    keep.sort(key=lambda x: (not x["short"], x["start"] or "", x["title"] or ""))
    save("latest/festivals.json", keep)

def festivals_std():
    """전국문화축제표준데이터(지자체 등록 축제) — 관광공사 목록에 없는 지역 축제 보완."""
    start = NOW.strftime("%Y-%m-%d"); end = (NOW + datetime.timedelta(days=21)).strftime("%Y-%m-%d")
    res, page = [], 1
    while page <= 20:
        q = urllib.parse.urlencode({"serviceKey": K, "type": "json", "numOfRows": 500, "pageNo": page})
        try:
            with urllib.request.urlopen("https://api.data.go.kr/openapi/tn_pubr_public_cltur_fstvl_api?" + q, timeout=40) as r:
                d = json.loads(r.read().decode("utf-8", "ignore"))
        except Exception as e:
            print("fail festivals_std", e); break
        it = items(d)
        if not it: break
        res += it; page += 1
        if len(it) < 500: break
    keep = [{"title": i.get("fstvlNm"), "start": i.get("fstvlStartDate"), "end": i.get("fstvlEndDate"), "place": i.get("opar"),
             "content": (i.get("fstvlCo") or "")[:120], "org": i.get("mnnstNm"), "addr": i.get("rdnmadr") or i.get("lnmadr"), "url": i.get("homepageUrl")}
            for i in res if (i.get("fstvlEndDate") or "0") >= start and (i.get("fstvlStartDate") or "9") <= end]
    keep.sort(key=lambda x: x["start"] or "")
    save("latest/festivals_local.json", keep)

SIGUNGU = {"평창": ("51", "51760"), "정선": ("51", "51770"), "홍천": ("51", "51720"), "속초": ("51", "51210"), "인제": ("51", "51810"),
           "춘천": ("51", "51110"), "강릉": ("51", "51150"), "무주": ("52", "52730"), "구례": ("46", "46730"), "제주": ("50", "50110")}
def congestion():
    out = {}
    for n, (a, s) in SIGUNGU.items():
        out[n] = [{"name": i.get("tAtsNm"), "date": i.get("baseYmd"), "rate": i.get("cnctrRate")} for i in items(get("/B551011/TatsCnctrRateService/tatsCnctrRatedList", dict(C, areaCd=a, signguCd=s, numOfRows=500)))]
        time.sleep(0.2)
    save("latest/congestion.json", out)

def paged(path, params, limit=3000):
    res, page = [], 1
    while len(res) < limit:
        it = items(get(path, dict(params, numOfRows=500, pageNo=page)))
        if not it: break
        res += it; page += 1
        if len(it) < 500: break
    return res

def reference():
    ref = os.path.join(ROOT, "data", "reference")
    if NOW.weekday() != 0 and os.path.exists(os.path.join(ref, "durunubi_courses.json")):
        return
    save("reference/durunubi_courses.json", [{k: c.get(k) for k in ("crsKorNm", "crsDstnc", "crsTotlRqrmHour", "crsLevel", "sigun", "brdDiv", "crsSummary", "crsTourInfo", "gpxpath")} for c in paged("/B551011/Durunubi/courseList", C)])
    save("reference/gocamping.json", [{k: c.get(k) for k in ("facltNm", "lineIntro", "addr1", "induty", "doNm", "sigunguNm", "animalCmgCl", "homepage", "resveUrl")} for c in paged("/B551011/GoCamping/basedList", C)])
    save("reference/barrier_free.json", [{k: c.get(k) for k in ("title", "addr1", "areacode", "contentid", "contenttypeid")} for c in paged("/B551011/KorWithService2/areaBasedList2", C)])

MTN = {1:"설악산",3:"오대산",5:"치악산",7:"태백산",13:"가리왕산",15:"두타산",40:"북한산",47:"도봉산",50:"용문산",51:"청계산",46:"명지산",43:"남한산성",53:"계룡산",57:"속리산",59:"월악산",61:"민주지산",62:"월출산",64:"지리산 노고단",65:"무등산",67:"조계산",75:"내장산",77:"덕유산",79:"대둔산",80:"마이산",86:"지리산 천왕봉",88:"가야산",90:"가지산",92:"신불산",95:"황매산",104:"금정산",105:"주왕산",107:"소백산",109:"청량산"}

def mountain_weather():
    kk = os.environ.get("KMA_KEY", "")
    if not kk:
        print("skip mountain_weather (KMA_KEY missing)"); return
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9, minutes=-40)
    h = max([x for x in (2, 5, 8, 11, 14, 17, 20, 23) if x <= now.hour], default=None)
    if h is None:
        now -= datetime.timedelta(days=1); h = 23
    bd, bt = now.strftime("%Y%m%d"), f"{h:02d}00"
    out = []
    for n, name in MTN.items():
        u = f"https://apihub.kma.go.kr/api/typ08/getMountainWeather?mountainNum={n}&base_date={bd}&base_time={bt}&authKey={kk}"
        d = None
        for _ in range(3):
            try:
                d = json.loads(urllib.request.urlopen(u, timeout=40).read()); break
            except Exception:
                time.sleep(2)
        if not isinstance(d, list) or not d:
            continue
        days = {}
        for x in d:
            day = days.setdefault(x["fcstBase"], {})
            c, v = x["category"], (x["fcstValue"] or "").strip()
            if c in ("SRE", "SSE"):
                day[c.lower()] = v; continue
            try: f = float(v)
            except ValueError:
                if c in ("PCP", "SNO") and "없음" not in v: day.setdefault(c.lower(), v)
                continue
            if c == "TMP":
                day["tmin"] = min(day.get("tmin", f), f); day["tmax"] = max(day.get("tmax", f), f)
            elif c in ("WSD", "POP", "SKY"):
                day[c.lower() + "_max"] = max(day.get(c.lower() + "_max", f), f)
        out.append({"no": n, "name": name, "station": d[0]["stn_nm"], "alt": d[0]["alt"], "days": days})
    save("latest/mountain_weather.json", {"base": bd + bt, "note": "기상청 산악예보(정상부). wsd m/s, pop %, sky 1맑음 3구름많음 4흐림", "mountains": out})

if __name__ == "__main__":
    if not K:
        raise SystemExit("DATA_GO_KR_KEY missing")
    for f in (festivals, festivals_std, weather, mountain_weather, congestion, reference):
        try: f()
        except Exception as e: print("ERROR", f.__name__, e)
