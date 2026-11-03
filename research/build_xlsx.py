"""research/ 의 CSV·MD를 합쳐 SANKIT_브랜드_수입사_지도.xlsx 생성. 사용: python3 research/build_xlsx.py"""
import csv, glob, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
D=os.path.dirname(os.path.abspath(__file__)); F='Arial'
H=PatternFill('solid',fgColor='0B4A2C'); HF=Font(name=F,bold=True,color='FFFFFF',size=10)
OK=PatternFill('solid',fgColor='DDEFE3'); TBD=PatternFill('solid',fgColor='FFF3CD'); GAP=PatternFill('solid',fgColor='F8D7DA')
thin=Side(style='thin',color='D0D0D0')
wb=Workbook(); first=True
def sheet(name,path,widths,status=None):
    global first
    rows=list(csv.reader(open(path,encoding='utf-8-sig')))
    ws=wb.active if first else wb.create_sheet(); first=False; ws.title=name
    for r in rows: ws.append(r)
    for c in ws[1]: c.fill=H;c.font=HF;c.alignment=Alignment(vertical='center',wrap_text=True)
    for row in ws.iter_rows(min_row=2):
        for c in row: c.font=Font(name=F,size=10);c.alignment=Alignment(vertical='top',wrap_text=True);c.border=Border(bottom=thin)
        if status is not None:
            v=str(row[status].value or '')
            row[status].fill=GAP if '공백' in v or '없음' in v else (TBD if '확인 필요' in v and not v.startswith('확인(') and not v.startswith('확인 (') and v!='확인' else OK)
    for i,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(i)].width=w
    ws.freeze_panes='C2'; ws.auto_filter.ref=ws.dimensions; ws.row_dimensions[1].height=28
sheet('브랜드_수입사_지도',os.path.join(D,'brand_map.csv'),[14,26,30,42,22,22,46,12],5)
hp=sorted(glob.glob(os.path.join(D,'hot_products_*.csv')))
for p in hp[-3:]:
    sheet('화제제품_'+os.path.basename(p)[13:20],p,[12,18,26,44,30,26,24,46],5)
ch=sorted(glob.glob(os.path.join(D,'changes_*.md')))
if ch:
    ws=wb.create_sheet('이달의_변화')
    for line in open(ch[-1],encoding='utf-8').read().splitlines(): ws.append([line])
    ws.column_dimensions['A'].width=150
    for row in ws.iter_rows():
        c=row[0]; c.alignment=Alignment(wrap_text=True,vertical='top')
        c.font=Font(name=F,size=12 if str(c.value).startswith('#') else 10,bold=str(c.value).startswith('#'))
out=os.path.join(D,'SANKIT_브랜드_수입사_지도.xlsx'); wb.save(out); print('saved',out)
