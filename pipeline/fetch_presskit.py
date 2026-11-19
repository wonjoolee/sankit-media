#!/usr/bin/env python3
"""Mynewsdesk 뉴스룸에서 보도용 사진을 조건과 함께 내려받는다.

사용법:
  python3 pipeline/fetch_presskit.py atomic head haglofs
  python3 pipeline/fetch_presskit.py atomic --max=8

중요 — 라이선스:
  Mynewsdesk 기본 라이선스는 'Media Use' 다. 기자·블로거가 쓸 수 있지만 조건이 둘이다.
    1) 내용을 수정하지 않는다 (crop, 글자 얹기, 색 보정 금지)
    2) 촬영자를 크레딧으로 표기한다
  그래서 받은 사진은 카드에 '통째로' 넣고, 글자는 사진 밖에 둔다. EDITORIAL 21절을 따른다.
  라이선스가 'Media Use' 가 아닌 파일은 받지 않고 skipped 로 남긴다.
"""
import json, os, re, sys, time
from playwright.sync_api import sync_playwright
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
OK_LICENSE = ('Media Use', 'Creative Commons', 'Public Domain', 'All free of charge')


def dismiss(pg):
    for sel in ('text=Yes', 'button:has-text("Yes")', 'a:has-text("Yes")'):
        try:
            pg.click(sel, timeout=2000)
            return
        except Exception:
            pass


def image_pages(pg, slug, want):
    pg.goto(f'https://www.mynewsdesk.com/{slug}/latest_media',
            wait_until='domcontentloaded', timeout=60000)
    dismiss(pg)
    pg.wait_for_timeout(2200)
    seen = []
    for _ in range(10):
        hrefs = pg.eval_on_selector_all('a[href]', 'e=>e.map(x=>x.href)')
        for h in hrefs:
            if re.search(r'/images/[^/]+-\d+$', h or '') and h not in seen:
                seen.append(h)
        if len(seen) >= want:
            break
        pg.mouse.wheel(0, 2600)
        pg.wait_for_timeout(900)
    return seen[:want]


def read_image(pg, url):
    pg.goto(url, wait_until='domcontentloaded', timeout=60000)
    dismiss(pg)
    pg.wait_for_timeout(1400)
    txt = pg.inner_text('body')
    links = pg.eval_on_selector_all('a[href]', 'e=>e.map(x=>x.href)')
    dl = [l for l in links if 'fl_attachment' in (l or '')]
    rec = {'page': url, 'download': dl[0] if dl else ''}

    m = re.search(r'License:\s*\n?\s*([^\n]+)', txt)
    rec['license'] = m.group(1).strip() if m else ''
    m = re.search(r'\n([^\n]+\.(?:jpg|jpeg|png|webp|tif))\n', txt, re.I)
    rec['filename'] = m.group(1).strip() if m else url.rsplit('/', 1)[-1] + '.jpg'
    m = re.search(r'Size:\s*\n?\s*([^\n]+)', txt)
    rec['size'] = m.group(1).strip() if m else ''
    m = re.search(r'(?:Photographer|Photo|Credit|Fotograf)\s*[:：]\s*\n?\s*([^\n]{2,80})', txt, re.I)
    rec['credit'] = m.group(1).strip() if m else ''
    m = re.search(r'(The content may be downloaded.{0,600}?)\n', txt, re.S)
    rec['terms'] = re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''
    m = re.search(r'\n(\d{1,2} [A-Z][a-z]+ \d{4})\n', txt)
    rec['published'] = m.group(1) if m else ''
    return rec


def main():
    slugs = [a for a in sys.argv[1:] if not a.startswith('--')]
    want = 6
    for a in sys.argv:
        if a.startswith('--max='):
            want = int(a.split('=')[1])
    if not slugs:
        print(__doc__)
        return

    month = time.strftime('%Y-%m')
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1400, 'height': 1000})
        for slug in slugs:
            outdir = os.path.join(ROOT, 'assets', 'press', slug, month)
            os.makedirs(outdir, exist_ok=True)
            pages = image_pages(pg, slug, want)
            print(f'[{slug}] 사진 페이지 {len(pages)}개')
            recs, skipped = [], []
            for u in pages:
                try:
                    r = read_image(pg, u)
                except Exception as e:
                    skipped.append({'page': u, 'why': f'읽기 실패 {e}'})
                    continue
                if not any(k.lower() in r['license'].lower() for k in OK_LICENSE):
                    skipped.append({'page': u, 'why': f"라이선스 '{r['license']}'"})
                    print(f"   - 건너뜀 ({r['license'] or '라이선스 표기 없음'})")
                    continue
                if not r['download']:
                    skipped.append({'page': u, 'why': '다운로드 링크 없음'})
                    continue
                safe = re.sub(r'[^A-Za-z0-9._-]', '_', r['filename'])[:90]
                dest = os.path.join(outdir, safe)
                try:
                    req = urllib.request.Request(r['download'], headers=UA)
                    data = urllib.request.urlopen(req, timeout=60).read()
                    open(dest, 'wb').write(data)
                    r['file'] = os.path.relpath(dest, ROOT)
                    r['bytes'] = len(data)
                    recs.append(r)
                    print(f"   + {safe}  {len(data)//1024}KB  [{r['license']}]")
                except Exception as e:
                    skipped.append({'page': u, 'why': f'내려받기 실패 {e}'})

            if recs:
                json.dump({'brand': slug, 'month': month, 'files': recs, 'skipped': skipped},
                          open(os.path.join(outdir, 'index.json'), 'w'),
                          ensure_ascii=False, indent=1)
                lic = recs[0]
                with open(os.path.join(outdir, 'LICENSE.txt'), 'w') as f:
                    f.write(f"""출처: Mynewsdesk 뉴스룸 — https://www.mynewsdesk.com/{slug}
수집일: {time.strftime('%Y-%m-%d')}
라이선스: {lic['license']}

조건 (원문):
{lic['terms']}

산킷이 지킬 것:
1. 사진을 수정하지 않는다. 자르지 않고, 글자를 얹지 않고, 색을 고치지 않는다.
   카드에는 사진을 통째로 넣고 글자는 사진 밖 영역에 둔다.
2. 촬영자 크레딧을 표기한다. 촬영자가 표기되지 않은 파일은 브랜드명을 출처로 적는다.
3. 광고가 아니다. 대가를 받은 글에 쓰는 경우에는 '광고' 표기 규칙을 따른다.

파일별 출처 페이지와 크레딧은 index.json 에 있다.
""")
                print(f'   -> {outdir}  ({len(recs)}장, 건너뜀 {len(skipped)})')
            else:
                print(f'   받은 사진이 없습니다 (건너뜀 {len(skipped)})')
        b.close()


if __name__ == '__main__':
    main()
