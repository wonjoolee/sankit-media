# 사용: python3 reel.py config.json out.mp4
# mode "own": 직접 찍은 사진·공공누리 사진 → 자르기 허용, 장면마다 다른 느린 움직임
# mode "press": 프레스 사진 → 자르기 없이 원본 비율 그대로(라이선스 '원본 비변형'), 전체를 아주 천천히 확대·축소만
#
# 2026-11-12 운영자 지적: 너무 짧고, 왼쪽→오른쪽 팬만 있어 지루하다. 더 천천히 움직여야 자연스럽다.
#  → 장면 최소 5.5초, 전환 1초, 엔딩 3초(사진 4장이면 약 22초)
#  → 움직임을 장면마다 바꾼다: 천천히 확대 / 오른쪽으로 흐름 / 천천히 축소 / 왼쪽으로 흐름 / 위로 올림
#     가로 사진은 한 번씩 '흐린 배경 + 사진 전체' 액자 장면으로 보여 준다
#  → 움직임 폭은 작게(확대 6~8%, 흐름은 사진 폭의 12% 이내), 처음과 끝은 부드럽게 감속(이즈 인·아웃)
#  → 글자는 1초에 걸쳐 천천히 떠오른다. 글자 묶음 아래 끝은 y 1500(피드 4:5 안).
import subprocess, sys, json, math, os
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
W, H, FPS = 1080, 1920, 30
BLK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'; MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
fb = ImageFont.truetype(BLK, 88, index=1); fk = ImageFont.truetype(BLK, 32, index=1); fw = ImageFont.truetype(BLK, 40, index=1); fm = ImageFont.truetype(MONO, 26)
cfg = json.load(open(sys.argv[1])); out = sys.argv[2]; mode = cfg['mode']; sc = cfg['scenes']
XF = 1.0; END = 3.0; MIN_SEC = 5.5
for s in sc:
    s['sec'] = max(float(s.get('sec', MIN_SEC)), MIN_SEC)
src = [ImageOps.exif_transpose(Image.open(s['img'])).convert('RGB') for s in sc]
dark = Image.new('RGB', (W, H), (20, 22, 21))

# 아래쪽 글자 받침 그라데이션 + 위쪽 워드마크 받침
grad = Image.new('L', (1, H), 0)
for y in range(H):
    a = int(215 * min(1, max(0, (y - H * .45) / (H * .38))) ** 1.2)
    if y < 420: a = max(a, int(110 * (1 - y / 420)))
    grad.putpixel((0, y), a)
grad = grad.resize((W, H))


def ease(p):  # 처음과 끝이 느린 곡선
    p = min(1, max(0, p))
    return 0.5 - 0.5 * math.cos(math.pi * p)


MOVES = ['zoom_in', 'drift_right', 'zoom_out', 'drift_left', 'rise']


def plan(i, im):
    """장면마다 움직임을 정한다. 가로 사진은 두 번째마다 액자 장면."""
    iw, ih = im.size
    landscape = iw / ih > 1.15
    if mode == 'own' and landscape and i % 2 == 1:
        return 'frame'
    return sc[i].get('move') or MOVES[i % len(MOVES)]


def crop_box(im, move, p):
    """9:16 잘라내기 창의 위치·크기(p=0~1, 이미 감속 곡선 적용)."""
    iw, ih = im.size
    base = min(iw / W, ih / H)              # 화면을 꽉 채우는 가장 큰 창의 배율
    cw0, ch0 = W * base, H * base
    if move == 'zoom_in':
        z = 1.0 + 0.08 * p; cx, cy = iw / 2, ih / 2
    elif move == 'zoom_out':
        z = 1.08 - 0.08 * p; cx, cy = iw / 2, ih / 2
    else:
        z = 1.06
    cw, ch = cw0 / z, ch0 / z
    room_x, room_y = iw - cw, ih - ch
    if move == 'drift_right':
        span = min(room_x, iw * 0.12); cx = iw / 2 - span / 2 + span * p; cy = ih / 2
    elif move == 'drift_left':
        span = min(room_x, iw * 0.12); cx = iw / 2 + span / 2 - span * p; cy = ih / 2
    elif move == 'rise':
        span = min(room_y, ih * 0.10); cx = iw / 2; cy = ih / 2 + span / 2 - span * p
    cx = min(max(cx, cw / 2), iw - cw / 2); cy = min(max(cy, ch / 2), ih - ch / 2)
    return (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)


# 장면별로 미리 준비(흐린 배경, 움직임)
prep = []
for i, im in enumerate(src):
    mv = 'press' if mode == 'press' else plan(i, im)
    bg = None
    if mv in ('frame', 'press'):
        k = max(W / im.width, H / im.height)
        bg = im.resize((int(im.width * k) + 2, int(im.height * k) + 2), Image.BICUBIC)
        bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
        bg = Image.blend(bg.filter(ImageFilter.GaussianBlur(40)), dark, 0.55 if mv == 'frame' else 0.85)
    prep.append((mv, bg))


def text(fr, s, t):
    a = ease(t / 1.0)                        # 1초에 걸쳐 떠오름
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((64, 320), 'SANKIT', font=fw, fill=(244, 242, 236, 255))
    n = len(s['lines']); y0 = 1500 - (58 + n * 108); rise = int((1 - a) * 24); al = int(255 * a)
    d.text((64, y0 + rise), s['kick'], font=fk, fill=(217, 164, 65, al))
    for j, l in enumerate(s['lines']):
        f = fb
        while d.textlength(l, font=f) > W - 180: f = ImageFont.truetype(BLK, f.size - 4, index=1)
        d.text((64, y0 + 58 + j * 108 + rise), l, font=f, fill=(244, 242, 236, al))
    _cr = cfg.get('credit', '@SANKITMAG'); d.text((64, 1530), _cr, font=(fm if _cr.isascii() else ImageFont.truetype(BLK, 26, index=1)), fill=(190, 192, 189, 255))
    fr.paste(lay, (0, 0), lay)


def frame(i, t):
    s = sc[i]; im = src[i]; mv, bg = prep[i]
    p = ease(t / (s['sec'] + XF))           # 전환 동안에도 계속 움직이게
    if mv == 'press':
        fr = bg.copy(); z = (1.0 + 0.04 * p) if i % 2 == 0 else (1.04 - 0.04 * p)
        k = min(1000 / im.width, 1150 / im.height) * z
        w, h = int(im.width * k), int(im.height * k)
        fr.paste(im.resize((w, h), Image.BICUBIC), ((W - w) // 2, 260 + (1150 - h) // 2))
    elif mv == 'frame':
        fr = bg.copy(); z = 1.0 + 0.05 * p
        w = int(W * z); h = int(im.height * w / im.width)
        ph = im.resize((w, h), Image.BICUBIC)
        fr.paste(ph, ((W - w) // 2, 760 - h // 2))
    else:
        fr = im.resize((W, H), Image.BICUBIC, box=crop_box(im, mv, p))
    fr = Image.composite(dark, fr, grad)
    text(fr, s, t)
    return fr


logo = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'logo.png')).convert('RGB').resize((600, 600), Image.LANCZOS)
mk = Image.new('L', (600, 600), 0); ImageDraw.Draw(mk).ellipse((0, 0, 599, 599), fill=255)
fk2 = ImageFont.truetype(BLK, 40, index=1)


def endf(t):
    fr = Image.new('RGB', (W, H), (11, 74, 44)); fr.paste(logo, (240, 480), mk); d = ImageDraw.Draw(fr)
    d.text((W // 2, 1230), cfg.get('end_line', '스키·아웃도어 소식, 한국에서 가장 빠르게'), font=fk2, fill=(243, 238, 223), anchor='mm')
    d.text((W // 2, 1300), cfg.get('end_follow', '팔로우해 두세요'), font=fk, fill=(242, 201, 76), anchor='mm')
    d.text((W // 2, 1370), '@SANKITMAG', font=fm, fill=(243, 238, 223), anchor='mm')
    return fr


st = []; acc = 0
for s in sc: st.append(acc); acc += s['sec'] - XF
es = acc + XF; tot = es + END
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-shortest', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
                       '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
for f in range(int(tot * FPS)):
    T = f / FPS
    last = len(sc) - 1
    if T >= es - XF:
        img = endf(T - es)
        if T < es: img = Image.blend(frame(last, T - st[last]), img, ease((T - (es - XF)) / XF))
    else:
        i = max(k for k, x in enumerate(st) if x <= T); img = frame(i, T - st[i])
        if i > 0 and T - st[i] < XF: img = Image.blend(frame(i - 1, T - st[i - 1]), img, ease((T - st[i]) / XF))
    ff.stdin.write(img.tobytes())
ff.stdin.close(); ff.wait(); print('reel', out, round(tot, 1), 's')
