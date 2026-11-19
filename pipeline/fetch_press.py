#!/usr/bin/env python3
"""뉴스와이어 분야별 RSS에서 산킷에 쓸 보도자료를 모아 쌓는다.

사용법:
  python3 pipeline/fetch_press.py            # 기본 피드 전부
  python3 pipeline/fetch_press.py --list     # 쌓인 것 요약만
출력:
  research/press_feed.json      기사별 본문·연락처·브랜드·이미지 URL
  research/press_contacts_new.csv  처음 본 회사의 연락처만 (수동 검토 후 press_contacts.csv로 옮김)
규칙:
  - 사진은 URL만 기록한다. file.newswire.co.kr 이 허용 목록에 들어오면 내려받는다.
  - 보도자료 사진은 매체 사용이 전제지만, 받을 때 LICENSE.txt 를 함께 쓴다(19절).
"""
import json, os, re, sys, time, html, urllib.request, urllib.parse
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'research', 'press_feed.json')
NEWC = os.path.join(ROOT, 'research', 'press_contacts_new.csv')
KNOWN = os.path.join(ROOT, 'research', 'press_contacts.csv')

FEEDS = {
    '1304': '야외 레저',
    '903':  '의류와 잡화',
}
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

# 산킷 주제: 산, 눈, 아웃도어 장비·의류
WANT = ['스키','스노보드','보드','슬로프','리프트','곤돌라','설산','설경','백컨트리','프리라이드',
        '등산','산행','트레킹','하이킹','등반','클라이밍','암벽','빙벽','볼더링','알파인',
        '캠핑','백패킹','야영','글램핑','텐트','타프','침낭','매트','버너','코펠','랜턴','헤드램프',
        '등산화','트레킹화','배낭','백팩','다운','재킷','자켓','플리스','소프트쉘','하드쉘','고어텍스',
        '아웃도어','산악','국립공원','자연휴양림','둘레길','트레일','트레일러닝','러닝',
        '피켈','아이젠','크램폰','하네스','카라비너','비콘','아발란치','폴','스틱','스노슈',
        '리조트','스키장','케이블카']
# 산킷 주제가 아닌 것
SKIP = ['골프','파크골프','보트','요트','수상레저','제트스키','서핑','스쿠버','다이빙','낚시','조어',
        '운세','박람회 운세','경마','카지노','볼링','당구','테니스','야구','축구','농구','배구',
        '펜션 예약','워터파크','수영장','헬스','필라테스','요가']

def get(url, tries=3, timeout=25):
    for a in range(tries):
        try:
            r = urllib.request.Request(url, headers=UA)
            return urllib.request.urlopen(r, timeout=timeout).read().decode('utf-8', 'replace')
        except Exception as e:
            if a == tries - 1:
                return None
            time.sleep(1.5 * (a + 1))

def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', s or ''))).strip()

def relevant(text):
    t = text
    if any(s in t for s in SKIP) and not any(w in t for w in WANT):
        return False, None
    hits = [w for w in WANT if w in t]
    return (len(hits) > 0), hits

def parse_article(no):
    url = f'https://www.newswire.co.kr/newsRead.php?no={no}'
    h = get(url)
    if not h:
        return None
    soup = BeautifulSoup(h, 'html.parser')
    main = soup.find('main') or soup
    text = main.get_text('\n', strip=True)

    rec = {'no': no, 'url': url}

    # 제목
    t = soup.find('title')
    rec['title'] = (t.get_text(strip=True).replace(' - 뉴스와이어', '') if t else '')

    # 본문 내 "문의:" 줄
    m = re.search(r'문의\s*[:：]\s*([^\n]{3,120})', text)
    rec['inline_contact'] = m.group(1).strip() if m else ''

    # 연락처 블록: '연락처' 이후 몇 줄
    blk = ''
    i = text.find('\n연락처\n')
    if i >= 0:
        blk = text[i + 5: i + 400]
    lines = [l.strip() for l in blk.split('\n') if l.strip()
             and l.strip() not in ('이메일 보내기',) and len(l.strip()) > 1][:6]
    rec['contact_block'] = lines
    # 연락처 블록 구조: [회사(+'홍보대행')] [대행사] [담당자] [전화]
    rec['agency'] = ''
    if lines and '홍보대행' in lines[0]:
        rec['org'] = lines[0].replace('홍보대행', '').strip()
        rec['agency'] = lines[1] if len(lines) > 1 else ''
        rec['person'] = lines[2] if len(lines) > 2 else ''
    else:
        rec['org'] = lines[0] if lines else ''
        rec['person'] = lines[2] if len(lines) > 2 else (lines[1] if len(lines) > 1 else '')

    # 전화
    rec['phones'] = sorted(set(
        m.group(1) for m in re.finditer(
            r'(?<![\d-])(0(?:2|[3-6][1-5]|70|1[016789])[-\s]\d{3,4}[-\s]\d{4})(?![\d-])', text)
    )) or sorted(set(
        m.group(1) for m in re.finditer(
            r'(?<![\d-])(1[5-6]\d{2}[-\s]?\d{4})(?![\d-])', text)))
    rec['emails'] = sorted(set(re.findall(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', text)))

    # '<회사> 개요' 블록 = 독점수입 브랜드가 적혀 있는 곳
    tl = text.split('\n')
    rec['company'] = ''
    rec['company_profile'] = ''
    for idx, ln in enumerate(tl):
        ls = ln.strip()
        if ls.endswith('개요') and 2 < len(ls) <= 34:
            rec['company'] = ls[:-2].strip()
            prof = []
            for nx in tl[idx + 1: idx + 10]:
                n = nx.strip()
                if not n or n.startswith(('웹사이트', '연락처', '관련 분야', '보도자료')):
                    break
                prof.append(n)
            rec['company_profile'] = re.sub(r'\s+', ' ', ' '.join(prof)).strip()
            break
    if not rec['company']:
        rec['company'] = rec.get('org') or (lines[0] if lines else '')

    # 웹사이트
    m = re.search(r'웹사이트\s*[:：]?\s*(https?://[^\s]+)', text)
    rec['website'] = m.group(1) if m else ''

    # 이미지 (지금은 URL만 기록)
    imgs = []
    for im in main.find_all('img'):
        s = im.get('src') or ''
        if 'file.newswire.co.kr' in s and '/thumb/' not in s:
            imgs.append(s)
    rec['images'] = sorted(set(imgs))

    rec['body'] = text[:4000]
    return rec

def backfill(cat, cat1, pages, label):
    """분야 목록 페이지를 거슬러 올라가며 기사 번호를 모은다."""
    nos = []
    for pg in range(1, pages + 1):
        u = (f'https://www.newswire.co.kr/?md=A01&cat={cat}&cat1={cat1}'
             f'&perpage=75&page={pg}')
        h = get(u)
        if not h:
            print(f'  [{label}] {pg}쪽 실패')
            continue
        soup = BeautifulSoup(h, 'html.parser')
        seen = {}
        for a in soup.find_all('a', href=True):
            m = re.search(r'newsRead\.php\?no=(\d+)', a['href'])
            if not m:
                continue
            txt = a.get_text(' ', strip=True)
            no = m.group(1)
            if txt and len(txt) > len(seen.get(no, '')):
                seen[no] = txt
        if not seen:
            print(f'  [{label}] {pg}쪽 기사 없음 — 멈춥니다')
            break
        print(f'  [{label}] {pg}쪽 기사 {len(seen)}개')
        nos += list(seen.items())
        time.sleep(0.6)
    out, got = [], set()
    for no, txt in nos:
        if no not in got:
            got.add(no)
            out.append((no, txt))
    return out


def main():
    store = {}
    if os.path.exists(OUT):
        try:
            store = {str(r['no']): r for r in json.load(open(OUT))}
        except Exception:
            store = {}
    before = len(store)

    known_orgs = set()
    if os.path.exists(KNOWN):
        for line in open(KNOWN):
            p = line.split(',')
            if len(p) > 2:
                known_orgs.add(p[2].strip())

    cand = []
    if '--backfill' in sys.argv:
        pages = 4
        for a in sys.argv:
            if a.startswith('--pages='):
                pages = int(a.split('=')[1])
        for cat, cat1, label in (('1300', '1304', '야외 레저'), ('900', '903', '의류와 잡화')):
            for no, txt in backfill(cat, cat1, pages, label):
                ok, hits = relevant(clean(txt))
                if ok:
                    cand.append((no, label + ' 백필', hits, clean(txt)[:80]))
        print(f'\n백필 후보 {len(cand)}건')

    for cid, label in FEEDS.items():
        xml = get(f'https://api.newswire.co.kr/rss/industry/{cid}')
        if not xml:
            print(f'  [{label}] 피드를 받지 못했습니다')
            continue
        items = re.findall(r'<item>(.*?)</item>', xml, re.S)
        print(f'  [{label}] 피드 {len(items)}건')
        for it in items:
            link = re.search(r'<link>(.*?)</link>', it)
            ti   = re.search(r'<title>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</title>', it, re.S)
            de   = re.search(r'<description>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</description>', it, re.S)
            if not link:
                continue
            no = re.search(r'no=(\d+)', link.group(1))
            if not no:
                continue
            blob = clean((ti.group(1) if ti else '') + ' ' + (de.group(1) if de else ''))
            ok, hits = relevant(blob)
            if ok:
                cand.append((no.group(1), label, hits, blob[:80]))

    print(f'\n주제에 맞는 것 {len(cand)}건')
    added = 0
    for no, label, hits, head in cand:
        if no in store:
            continue
        rec = parse_article(no)
        if not rec:
            print(f'  x {no} 본문을 받지 못했습니다')
            continue
        rec['feed'] = label
        rec['keywords'] = hits
        store[no] = rec
        added += 1
        print(f'  + {no} {rec["title"][:46]}  | {rec["company"][:16]} | {",".join(rec["phones"][:1])}')

    rows = sorted(store.values(), key=lambda r: -int(r['no']))
    json.dump(rows, open(OUT, 'w'), ensure_ascii=False, indent=1)

    # 처음 본 회사만 따로
    new, seen_org = [], set()
    for r in rows:
        org = r.get('company', '').strip()
        if org in seen_org:
            continue
        if org and org not in known_orgs and (r['phones'] or r['emails']):
            seen_org.add(org)
            new.append([org, r.get('agency', ''), r.get('person', ''),
                        (r['emails'] or [''])[0], (r['phones'] or [''])[0],
                        r['website'], r['url'], r.get('company_profile', '')[:180]])
    if new:
        with open(NEWC, 'w') as f:
            f.write('조직,홍보대행사,담당,이메일,전화,웹사이트,근거URL,회사개요\n')
            for n in new:
                f.write(','.join('"' + str(x).replace('"', "'") + '"' for x in n) + '\n')

    print(f'\n쌓인 기사 {before} -> {len(store)} (새로 {added}건)')
    print(f'처음 본 회사 {len(new)}곳 -> research/press_contacts_new.csv')

if __name__ == '__main__':
    main()
