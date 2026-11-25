#!/usr/bin/env python3
"""산킷 뉴스 릴스 — 한 줄씩 끊어 보여주는 타이포 영상.

  python3 pipeline/news_reel.py <슬롯폴더> [YYYY-MM-DD]

카드 한 장을 화면에 띄워 넘기는 릴스가 아니다(EDITORIAL 10절 금지).
한 장면에 한 가지 사실만 띄우고, 마지막에 팔로우 이유를 둔다.
"""
import json, os, re, subprocess, sys
from datetime import date

N_BEATS = 7          # 영상에 싣는 줄 수. 다 넣지 않는다 — 나머지는 카드에서 본다.
SEC_TITLE, SEC_BEAT, SEC_END = 1.8, 2.3, 2.6
W, H = 1080, 1920
WD = ['월','화','수','목','금','토','일']

def frames_html(d0, beats):
    css = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#000;font-family:'Noto Sans CJK KR','Noto Sans CJK JP','Noto Color Emoji',sans-serif}
.f{width:1080px;height:1920px;position:relative;overflow:hidden;background:#F4F2EC;color:#141615}
.wm{position:absolute;left:70px;top:70px;font-size:30px;font-weight:900;letter-spacing:10px}
.wm i{font-style:normal;font-weight:300;letter-spacing:4px;margin-left:10px;font-size:.55em;vertical-align:middle}
.mono{font-family:'DejaVu Sans Mono',monospace}
.tag{position:absolute;right:70px;top:76px;font-size:22px;letter-spacing:4px;color:#8a5521;font-weight:700}
.no{position:absolute;left:70px;top:300px;font-size:150px;font-weight:700;color:#8a5521;letter-spacing:2px;line-height:1}
.tx{position:absolute;left:70px;right:70px;top:520px;height:740px;display:flex;align-items:center;font-size:70px;font-weight:800;line-height:1.34;letter-spacing:-2.5px;word-break:keep-all;overflow-wrap:break-word}
.tx b{font-weight:800;color:#8a5521}
.ft{position:absolute;left:70px;bottom:80px;font-size:24px;letter-spacing:4px;color:#8a8d8a}
.tt{position:absolute;left:70px;right:70px;top:620px}
.tt .k{font-size:34px;letter-spacing:6px;color:#8a5521;font-weight:700;margin-bottom:24px}
.tt .d{font-size:150px;font-weight:800;letter-spacing:-5px;line-height:1.05}
.tt .s{font-size:40px;font-weight:700;color:#5d615e;margin-top:28px;letter-spacing:-1px}
.end{position:absolute;left:70px;right:70px;top:640px}
.end .a{font-size:86px;font-weight:800;letter-spacing:-3px;line-height:1.25}
.end .b{font-size:36px;font-weight:700;color:#5d615e;margin-top:40px;line-height:1.5;letter-spacing:-1px}
"""
    out = [f'<!doctype html><meta charset="utf-8"><style>{css}</style>']
    out.append(f'''<div class="f" id="f0"><div class="wm">SANKIT<i>산킷</i></div>
      <div class="tag mono">NEWS</div>
      <div class="tt"><div class="k">오늘의 산 · 오늘의 눈</div>
        <div class="d">{d0.month}월 {d0.day}일</div>
        <div class="s">{WD[d0.weekday()]}요일 · 스키장 날씨와 국내외 업계 소식</div></div>
      <div class="ft mono">SANKIT · NEWS</div></div>''')
    for i, b in enumerate(beats, 1):
        out.append(f'''<div class="f" id="f{i}"><div class="wm">SANKIT<i>산킷</i></div>
          <div class="tag mono">{d0.month:02d}.{d0.day:02d}</div>
          <div class="no mono">{i:02d}</div>
          <div class="tx"><span>{b}</span></div>
          <div class="ft mono">SANKIT · NEWS</div></div>''')
    out.append(f'''<div class="f" id="f{len(beats)+1}"><div class="wm">SANKIT<i>산킷</i></div>
      <div class="tag mono">NEWS</div>
      <div class="end"><div class="a">매일 아침 7시 30분,<br>한 장으로 끝냅니다</div>
        <div class="b">스키장 날씨와 국내외 업계 소식을<br>산킷이 매일 모아 드립니다.<br>@sankitmag</div></div>
      <div class="ft mono">SANKIT · NEWS</div></div>''')
    return '\n'.join(out)

def main(outdir, d0):
    n = json.load(open('data/latest/news_lines.json'))
    lines = [l for l in n['lines'] if not l.startswith('## ')]
    beats = lines[:N_BEATS]

    html = os.path.join(outdir, 'reel.html')
    open(html, 'w', encoding='utf-8').write(frames_html(d0, beats))

    ids = ['f0'] + [f'f{i}' for i in range(1, len(beats) + 1)] + [f'f{len(beats)+1}']
    subprocess.run(['node', '-e', f'''
const {{chromium}}=require('playwright');
(async()=>{{const b=await chromium.launch();
const p=await b.newPage({{viewport:{{width:1080,height:1920}}}});
await p.goto('file://{os.path.abspath(html)}');await p.waitForTimeout(900);
for (const id of {json.dumps(ids)}) await p.locator('#'+id).screenshot({{path:'{outdir}/_'+id+'.png'}});
await b.close();}})()'''], check=True)

    segs = []
    for j, fid in enumerate(ids):
        sec = SEC_TITLE if j == 0 else (SEC_END if j == len(ids) - 1 else SEC_BEAT)
        mp4 = f'{outdir}/_{fid}.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', f'{outdir}/_{fid}.png',
                        '-t', str(sec), '-vf',
                        'fade=t=in:st=0:d=0.22,format=yuv420p',
                        '-r', '30', '-c:v', 'libx264', '-crf', '20', mp4], check=True)
        segs.append(mp4)

    lst = os.path.join(outdir, '_cc.txt')
    open(lst, 'w').write(''.join(f"file '{os.path.basename(s)}'\n" for s in segs))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '30', '-crf', '21', '-an',
                    os.path.join(outdir, 'reel.mp4')], check=True, cwd=outdir)

    for f in os.listdir(outdir):
        if f.startswith('_'):
            os.remove(os.path.join(outdir, f))
    os.remove(html)
    total = SEC_TITLE + SEC_BEAT * len(beats) + SEC_END
    print(f'REEL {outdir}/reel.mp4  장면 {len(ids)}개 · {total:.1f}초')

if __name__ == '__main__':
    d0 = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    main(sys.argv[1], d0)
