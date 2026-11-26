from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFilter,ImageEnhance
# Reviewed coordinates in downscaled reference frames; exact source SHA required.
SPECS={
'hero-session.webp': ((1006,850),'190ddbb1d6cf8942c490f4d35ff458a418b42aacd7c992c978ccb277a567c717',None,[(690,229,735,268),(294,584,330,620),(385,600,416,643),(543,488,576,517),(655,481,683,523),(810,490,844,528),(852,581,882,624)]),
'community.webp': ((1100,825),'bafe57c5942f8da9cf35d02f9e2338d8252c970f8ce704736948d704ca95acdc',None,[(224,132,282,206),(184,248,261,324),(338,224,393,290),(502,252,562,319),(651,193,704,263),(777,254,839,324),(924,237,987,307)]),
'festival.webp': ((1100,827),'9ddc13f1df9aa2e1789b6003ca6f415cc3bced8766bd714e756e3a3956e4722b',None,[(128,321,176,377),(310,301,357,356),(423,291,469,348),(516,305,557,361),(635,324,683,380),(784,253,826,322),(929,308,977,367),(339,477,393,541),(494,505,557,569),(650,473,703,536)]),
'outdoor-community.webp': ((1100,620),'df22893337d674f973d3e2346031d82765bf94594ba1cac6ef06f27baf52bbe3',(0,0,845,620),[(52,229,89,267),(165,292,221,342),(185,134,218,172),(269,195,290,218),(323,155,351,184),(393,185,432,224),(558,180,602,225),(725,224,795,281),(827,170,849,204),(90,162,109,181)]),
'street-performance.webp': ((567,850),'3cb7bfcc6dfc9dbe692eb206953ad1e2430a6e13613eb8a3964c92802ffa0614',None,[(77,327,116,384),(218,266,265,324),(287,324,318,364),(347,317,390,368),(455,337,489,377),(513,339,548,388),(32,386,62,425),(0,401,17,435),(428,405,446,431)])}
GRADE={'hero-session.webp':(.86,.96),'community.webp':(.91,.97),'festival.webp':(.82,.96),'outdoor-community.webp':(.93,.98),'street-performance.webp':(.88,.98)}
def process(root=Path('assets'),report_path=Path('privacy-review.json')):
    report=[]
    for name,(ref,expected,crop,boxes) in SPECS.items():
        p=root/name; before=hashlib.sha256(p.read_bytes()).hexdigest()
        if before!=expected: raise ValueError(f'Unreviewed source: {name}')
        with Image.open(p) as src: im=src.convert('RGB')
        sx,sy=im.width/ref[0],im.height/ref[1]
        def scale(b): return tuple(round(v*(sx if i%2==0 else sy)) for i,v in enumerate(b))
        for b in boxes:
            x0,y0,x1,y1=scale(b); d=min(x1-x0,y1-y0); pad=max(3,round(d*.20)); ext=pad*3
            region=(max(0,x0-ext),max(0,y0-ext),min(im.width,x1+ext),min(im.height,y1+ext))
            patch=im.crop(region); mask=Image.new('L',patch.size)
            ImageDraw.Draw(mask).ellipse((x0-region[0]-pad,y0-region[1]-pad,x1-region[0]+pad,y1-region[1]+pad),fill=255)
            mask=mask.filter(ImageFilter.GaussianBlur(max(2,d*.09)))
            im.paste(patch.filter(ImageFilter.GaussianBlur(max(4,d*.25))),region,mask)
        if crop: im=im.crop(scale(crop))
        sat,contrast=GRADE[name]; im=ImageEnhance.Color(im).enhance(sat); im=ImageEnhance.Contrast(im).enhance(contrast)
        im.save(p,'WEBP',quality=84,method=6)
        report.append(dict(file=name,regions=len(boxes),source_sha256=before,derivative_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=list(im.size),review='manual_candidate_v4'))
    report_path.write_text(json.dumps(report,indent=2)); print(json.dumps(report))
if __name__=='__main__': process()
