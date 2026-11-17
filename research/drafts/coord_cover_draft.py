INK='#141615'; PAPER='#F4F2EC'; GR='#0B4A2C'; GOLD='#F2C94C'; BLUE='#BCD9EA'; OR='#E4603A'
css=f'''*{{box-sizing:border-box;margin:0;padding:0}}body{{background:#777;font-family:'Noto Sans CJK KR',sans-serif;padding:40px;display:flex;gap:40px;width:2320px}}
.card{{width:1080px;height:1350px;position:relative;overflow:hidden;background:{INK};color:{PAPER}}} .a{{position:absolute}}
.wm{{left:56px;top:50px;font-size:28px;font-weight:900;letter-spacing:10px}} .wm i{{font-style:normal;font-weight:300;letter-spacing:4px;margin-left:10px;font-size:.55em;vertical-align:middle}}
.ser{{right:56px;top:46px;background:{GOLD};color:{INK};font-size:22px;font-weight:900;padding:7px 18px;border-radius:30px}}
.ti{{left:56px;top:104px;font-size:84px;font-weight:900;letter-spacing:-4px;line-height:1.1}}
.su{{left:60px;top:212px;font-size:27px;font-weight:700;color:{GOLD};letter-spacing:-.5px}}
.q{{border-radius:18px}} .qt{{font-size:38px;font-weight:900;letter-spacing:-2px;line-height:1.15}} .qs{{font-size:20px;font-weight:700;letter-spacing:-.5px;margin-top:6px;opacity:.8}}
.pill{{transform:translate(-50%,-50%);background:#fff;color:{INK};border-radius:14px;padding:9px 20px 10px;white-space:nowrap;text-align:center;box-shadow:0 3px 0 rgba(20,22,21,.28)}}
.pill b{{display:block;font-size:34px;font-weight:900;letter-spacing:-1.5px;line-height:38px}}
.pill span{{display:block;font-size:17px;font-weight:500;color:#5d615e;line-height:21px;letter-spacing:-.3px}}
.logo{{height:44px;background:repeating-linear-gradient(45deg,#dcd9d0,#dcd9d0 7px,#ebe9e3 7px,#ebe9e3 14px);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:800;color:#8d8a80;letter-spacing:1px;margin-bottom:5px}}
.axc{{transform:translate(-50%,-50%);background:{INK};color:{PAPER};font-size:19px;font-weight:800;padding:6px 16px;border-radius:30px;white-space:nowrap;letter-spacing:-.3px}}
.leg{{left:56px;top:1222px;font-size:22px;font-weight:700;display:flex;gap:30px;letter-spacing:-.5px}} .leg i{{font-style:normal;margin-right:8px}}
.crit{{left:56px;right:56px;top:1268px;font-size:17px;line-height:1.6;color:#a9ada9;letter-spacing:-.3px}}
.stamp{{right:56px;top:112px;transform:rotate(5deg);background:#c0392b;color:#fff;font-size:21px;font-weight:900;padding:8px 14px;line-height:1.25;text-align:center;border-radius:6px}}'''
L,R,T,B=40,1040,268,1196; G=8; mx,my=560,700
X=lambda p:150+(p-100)/150*780; Y=lambda w:1130-(w-65)/36*800
pts=[('엘란','Wingman 86',87,108,120),('살로몬','QST 98',95,112,118),('노르디카','Enforcer 94',91,138,142),('블리자드','Rustler 9',97,150,138),
('뵐클','Deacon 76',77,116,96),('피셔','RC One 82 GT',80,144,150),('헤드','Supershape e-Magnum',73,150,196),('로시뇰','Hero Elite ST',70,118,142),
('아토믹','Redster S9',76,200,134),('오가사카','TC-S',68,205,116),('스톡클리','Laser SC',73,238,136),('케슬레','MX83',88,214,116),('DPS','Pagoda 100',96,240,124)]
def card(idx, logo):
    h=f'<div class="card" id="s{idx}"><div class="a wm">SANKIT<i>산킷</i></div><div class="a ser">산킷 좌표 01</div><div class="a stamp">시안<br>자리만 잡은 것</div>'
    h+='<div class="a ti">내 스키는 어디쯤일까</div><div class="a su">국내가 × 허리 폭으로 놓아 본 26/27 스키 13대</div>'
    Q=[(L,T,mx-G/2,my-G/2,BLUE,INK,'어디든 가 보는 한 대','넓은 허리 · 부담 적은 값','lt'),(mx+G/2,T,R,my-G/2,GR,PAPER,'깊은 눈까지 가는 한 대','넓은 허리 · 높은 값','rt'),
       (L,my+G/2,mx-G/2,B,GOLD,INK,'첫 카빙에 충분한 한 대','좁은 허리 · 부담 적은 값','lb'),(mx+G/2,my+G/2,R,B,OR,'#fff','다진 눈을 파고드는 한 대','좁은 허리 · 높은 값','rb')]
    for x0,y0,x1,y1,c,tc,t,s,pos in Q:
        h+=f'<div class="a q" style="left:{x0}px;top:{y0}px;width:{x1-x0}px;height:{y1-y0}px;background:{c}"></div>'
        st=('left:%dpx;'%(x0+24) if pos[0]=='l' else 'right:%dpx;text-align:right;'%(1080-x1+24))+('top:%dpx'%(y0+18) if pos[1]=='t' else 'top:%dpx'%(y1-92))
        h+=f'<div class="a" style="{st};color:{tc}"><div class="qt">{t}</div><div class="qs">{s}</div></div>'
    for k,m,w,p,lw in pts:
        inner=f'<div class="logo" style="width:{lw}px">로고</div>' if logo else f'<b>{k}</b>'
        h+=f'<div class="a pill" style="left:{X(p):.0f}px;top:{Y(w):.0f}px">{inner}<span>{m}</span></div>'
    h+=f'<div class="a axc" style="left:{mx}px;top:{T+2}px">↑ 허리가 넓다</div><div class="a axc" style="left:{mx}px;top:{B-2}px">↓ 허리가 좁다</div>'
    h+=f'<div class="a axc" style="left:{L+70}px;top:{my}px">← 덜 비싸다</div><div class="a axc" style="left:{R-64}px;top:{my}px">비싸다 →</div>'
    h+=f'<div class="a leg"><span><i>●</i>한국에서 살 수 있음</span><span><i>○</i>아직 한국에 없음</span><span><i style="color:{GOLD}">★</i>에디터가 직접 써 봄</span></div>'
    h+='<div class="a crit">기준: 공식몰 정가(바인딩 포함) 기준으로 놓음 · 확인일 2026.11.00 · 틀린 자리는 DM으로, 확인되면 고친 판을 다시 올립니다 <span style="float:right;color:#F4F2EC;font-weight:800">@sankitmag</span></div></div>'
    return h
open('chart.html','w').write(f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{css}</style></head><body>{card(1,False)}{card(2,True)}</body></html>')
