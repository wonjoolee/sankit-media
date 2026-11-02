# 사용: python3 reel.py config.json out.mp4
# mode "own": 직접 찍은 사진 → 확대/흐름 움직임
# mode "press": 프레스 사진 → 자르기·확대 없이 원본 비율 그대로(라이선스 '원본 비변형')
import subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageOps
W,H,FPS=1080,1920,30
BLK='/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'; MONO='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
fb=ImageFont.truetype(BLK,88,index=1); fk=ImageFont.truetype(BLK,32,index=1); fw=ImageFont.truetype(BLK,40,index=1); fm=ImageFont.truetype(MONO,26)
cfg=json.load(open(sys.argv[1])); out=sys.argv[2]; mode=cfg['mode']; sc=cfg['scenes']; XF=0.5; END=2.6
src=[ImageOps.exif_transpose(Image.open(s['img'])).convert('RGB') for s in sc]
dark=Image.new('RGB',(W,H),(20,22,21))
grad=Image.new('L',(1,H),0)
for y in range(H): grad.putpixel((0,y),int(210*max(0,(y-H*.55)/(H*.45))**1.3))
grad=grad.resize((W,H))
def text(fr,s,t,a):
    d=ImageDraw.Draw(fr); d.text((64,96),'SANKIT',font=fw,fill=(244,242,236))
    y0=H-470; d.text((64,y0),s['kick'],font=fk,fill=(217,164,65))
    for j,l in enumerate(s['lines']): d.text((64,y0+58+j*108+int((1-a)*30)),l,font=fb,fill=(244,242,236))
    d.text((64,H-120),cfg.get('credit','@SANKITMAG'),font=fm,fill=(190,192,189))
def frame(i,t):
    s=sc[i];im=src[i];iw,ih=im.size;p=min(1,max(0,t/s['sec']));a=min(1,t/.6)
    if mode=='press':
        fr=dark.copy(); k=min(1000/iw,1150/ih); w,h=int(iw*k),int(ih*k)
        fr.paste(im.resize((w,h),Image.LANCZOS),((W-w)//2,200+(1150-h)//2))
    else:
        if iw/ih<W/H*1.2:
            s0=max(W/iw,H/ih);z=1+.1*p;cw,ch=W/(s0*z),H/(s0*z);cx,cy=iw/2,ih/2
        else:
            s0=H/ih;cw,ch=W/s0,H/s0;cx=cw/2+(iw-cw)*(.15+.7*p);cy=ih/2
        fr=im.resize((W,H),Image.BILINEAR,box=(cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2))
        fr=Image.composite(dark,fr,grad)
    text(fr,s,t,a); return fr
logo=Image.open(''+__import__('os').path.join(__import__('os').path.dirname(__file__),'assets','logo.png')+'').convert('RGB').resize((640,640),Image.LANCZOS)
mk=Image.new('L',(640,640),0);ImageDraw.Draw(mk).ellipse((0,0,639,639),fill=255)
def endf(t):
    fr=Image.new('RGB',(W,H),(11,74,44));fr.paste(logo,(220,560),mk);d=ImageDraw.Draw(fr)
    d.text((W//2,1320),'안목과 취향으로 고른 장비',font=fk,fill=(243,238,223),anchor='mm');d.text((W//2,1380),'@SANKITMAG',font=fm,fill=(243,238,223),anchor='mm');return fr
st=[];acc=0
for s in sc: st.append(acc);acc+=s['sec']-XF
es=acc;tot=es+END
ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-f','lavfi','-i','anullsrc=r=44100:cl=stereo','-shortest','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',out],stdin=subprocess.PIPE)
for f in range(int(tot*FPS)):
    T=f/FPS
    if T>=es:
        img=endf(T-es)
        if T-es<XF: img=Image.blend(frame(len(sc)-1,T-st[-1]),img,(T-es)/XF)
    else:
        i=max(k for k,x in enumerate(st) if x<=T);img=frame(i,T-st[i])
        if i>0 and T-st[i]<XF: img=Image.blend(frame(i-1,T-st[i-1]),img,(T-st[i])/XF)
    ff.stdin.write(img.tobytes())
ff.stdin.close();ff.wait();print('reel',out,round(tot,1),'s')
