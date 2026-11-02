# 사용: python3 pipeline/to_jpg.py <폴더>  — 0N.png → 0N.jpg 변환 후 png 삭제 + 미리보기 sheet.jpg
import sys,glob,os
from PIL import Image
d=sys.argv[1];fs=sorted(glob.glob(os.path.join(d,'0[1-5].png')))
ims=[]
for f in fs:
    im=Image.open(f).convert('RGB');im.save(f[:-4]+'.jpg',quality=92);os.remove(f);ims.append(im)
w,h=540,675;s=Image.new('RGB',(20+(w+20)*len(ims),h+40),'#cccccc')
for i,im in enumerate(ims): s.paste(im.resize((w,h),Image.LANCZOS),(20+i*(w+20),20))
os.makedirs('/tmp/sankit_preview',exist_ok=True);s.save(f'/tmp/sankit_preview/{os.path.basename(os.path.dirname(d))}_{os.path.basename(d)}.jpg',quality=85)
print('ok',len(ims))
