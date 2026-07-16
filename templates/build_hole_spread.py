from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
from pathlib import Path

R=Path(__file__).parent
W,H=1600,1400  # 8 x 7-inch open spread at 200 dpi
P=800
paper=(244,241,232); ink=(27,34,29); green=(27,88,53); rule=(184,180,169); water=(47,79,88)
im=Image.new('RGB',(W,H),(17,24,19)); d=ImageDraw.Draw(im)
d.rectangle((20,20,W-20,H-20),fill=paper)
d.line((P,20,P,H-20),fill=(205,200,188),width=3)
art=Image.open(R/'hole-1-watercolor.png').convert('RGB')

def font(size,bold=False,serif=False):
    if serif:
        name='/usr/share/fonts/truetype/dejavu/DejaVuSerif%s.ttf'%('-Bold' if bold else '')
    else:
        name='/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'%('-Bold' if bold else '')
    return ImageFont.truetype(name,size)
def text(x,y,s,size=18,bold=False,fill=ink,serif=False,anchor=None): d.text((x,y),s,font=font(size,bold,serif),fill=fill,anchor=anchor)
def line(x1,y1,x2,y2,w=1): d.line((x1,y1,x2,y2),fill=rule,width=w)
def heading(x,y,s): text(x,y,s.upper(),15,True); return y+28
def note_lines(x,y,w,n=4,step=38):
    for i in range(n): line(x,y+i*step,x+w,y+i*step)

x=48;y=48
text(x,y,'OLD LYME',22,True,serif=True); text(x,y+28,'COUNTRY CLUB',22,True,serif=True)
text(x,y+64,'FIELD GUIDE SERIES',12,True,fill=green); line(x,y+92,275,y+92)
y+=122; text(x,y,'HOLE',15,True); text(x,y+22,'1',104,True,green,True)
text(x,y+132,'PAR 4',20,True); text(x+110,y+132,'INDEX 7',15,True); line(x,y+170,275,y+170)
y+=198; y=heading(x,y,'Today'); text(x,y,'DATE',11,True); line(x,y+32,150,y+32); text(170,y,'TEE TIME',11,True); line(170,y+32,275,y+32)
y+=72; y=heading(x,y,'At a glance')
for a,b in [('WHITE TEE','330 YDS'),('GARMIN','318 / 328 / 338'),('PAR','4'),('HANDICAP','7')]:
    text(x,y,a,12); text(275,y,b,12,True,anchor='ra'); y+=30
line(x,y+4,275,y+4); y+=30; y=heading(x,y,'Conditions'); text(x,y,'WIND',11,True); line(x,y+32,150,y+32); text(170,y,'WEATHER',11,True); line(170,y+32,275,y+32)
y+=72; y=heading(x,y,'Shot strategy')
for s in ['Controlled tee ball to','the widest landing area.','Play from the fairway.','Water guards the green.','No right fairway bunker.','Carries: field verify.']:
    text(x,y,s,12); y+=24
line(x,y+10,275,y+10); y+=38
text(x,y,'“Start smart.',15,False,serif=True); text(x,y+24,'Leave a clean number.”',15,False,serif=True)
y+=90; y=heading(x,y,'Round notes'); note_lines(x,y,227,5,36)

mx,my,mw,mh=300,82,470,1245
text(mx+mw//2,45,'TO GREEN CENTER',13,True,anchor='ma')
for xx,lab,val,col in [(mx+65,'FRONT','318',ink),(mx+mw//2,'WHITE','330',green),(mx+mw-65,'BACK','338',ink)]:
    text(xx,66,lab,10,True,anchor='ma'); text(xx,83,val,27,False,col,True,anchor='ma')
mapimg=ImageOps.contain(art,(mw,mh),Image.Resampling.LANCZOS)
im.paste(mapimg,(mx+(mw-mapimg.width)//2,my+(mh-mapimg.height)//2))
text(mx+mw//2,1340,'GEOMETRY FROM 2026 DRONE SURVEY',10,True,fill=(92,96,89),anchor='ma')

rx=840; text(rx,50,'GREEN OVERVIEW',19,True)
text(1545,54,'HOLE 1',12,True,fill=green,anchor='ra'); line(rx,83,1550,83)
crop=art.crop((0,0,art.width,int(art.height*.43)))
crop=ImageOps.fit(crop,(710,420),Image.Resampling.LANCZOS,centering=(.5,.28))
im.paste(ImageEnhance.Color(crop).enhance(.9),(rx,105))
text(rx+16,490,'GREEN DIMENSIONS & PIN ZONES — FIELD VERIFY',11,True,fill=paper)
line(rx,550,1550,550)
def cell(x,y,w,h,title,lines_,checks=False):
    text(x,y,title.upper(),14,True); yy=y+34
    for s in lines_:
        text(x,yy,('□  ' if checks else '')+s,13); yy+=28
    line(x,y+h,x+w,y+h)
cell(rx,575,335,180,'Green notes',['Water borders the right side','of the green complex.','Slope and depth: field verify.'])
line(1190,565,1190,755)
cell(1220,575,330,180,'Safe miss',['Play away from the pond.','Preferred recovery zone:','field verify.'])
cell(rx,785,335,190,'Targets & landmarks',['Landing widths and carries','will be added from GPS','and field measurements.'])
line(1190,775,1190,975)
cell(1220,785,330,190,"Today's game plan",['Club from tee: ______','Target: ____________','Leave favorite yardage','Middle of green'],True)
text(rx,1010,'PERSONAL NOTES',14,True); note_lines(rx,1050,335,7,40)
line(1190,1000,1190,1325)
text(1220,1010,'SHOT RECORD',14,True)
for i,label in enumerate(['TEE','APPROACH','CHIP / PUTT','RESULT']):
    yy=1050+i*68; text(1220,yy,label,11,True); line(1320,yy+20,1548,yy+20)
text(rx,1342,'OLD LYME CC · TOUR FIELD MANUAL',10,True,fill=(95,99,92))
text(1548,1342,'4 × 7 IN. PAGES · V0.2',10,True,fill=(95,99,92),anchor='ra')
im.save(R/'hole-1-approved-spread.png',quality=95)
