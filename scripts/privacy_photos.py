from pathlib import Path
import hashlib, json
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
# Face rectangles in the inspected reference coordinate frame, before crop.
SPECS = {
 'community.webp': ((1440,1080), 'bafe57c5942f8da9cf35d02f9e2338d8252c970f8ce704736948d704ca95acdc', None, [(287,166,371,270),(242,322,356,432),(439,285,520,382),(654,324,743,428),(840,251,925,342),(1016,330,1100,426),(1205,294,1313,400)]),
 'festival.webp': ((1404,1056), '9ddc13f1df9aa2e1789b6003ca6f415cc3bced8766bd714e756e3a3956e4722b', None, [(151,407,230,491),(393,377,464,464),(532,370,608,451),(647,379,716,463),(814,405,877,490),(995,321,1063,416),(1175,389,1256,479),(434,602,508,693),(626,646,715,750),(827,601,907,689)]),
 'hero-session.webp': ((1344,1135), '190ddbb1d6cf8942c490f4d35ff458a418b42aacd7c992c978ccb277a567c717', None, [(924,307,970,359),(393,778,440,829),(510,805,554,860),(716,652,767,697),(874,647,916,701),(1084,661,1126,708),(1138,779,1190,832)]),
 'outdoor-community.webp': ((1600,902), 'df22893337d674f973d3e2346031d82765bf94594ba1cac6ef06f27baf52bbe3', (0,0,1265,902), [(78,336,128,391),(241,431,325,509),(269,196,313,248),(391,284,425,321),(476,235,514,273),(576,279,627,327),(811,266,861,320),(1060,324,1144,400),(1200,249,1235,291),(132,234,159,265)]),
 'street-performance.webp': ((1000,1500), '3cb7bfcc6dfc9dbe692eb206953ad1e2430a6e13613eb8a3964c92802ffa0614', None, [(130,583,201,683),(377,485,454,569),(509,585,557,653),(614,566,686,652),(799,601,855,657),(905,603,965,678),(69,680,115,742),(0,720,29,776),(757,709,790,744)])
}

# Per-image saturation, contrast and warmth; subtle matte editorial palette.
GRADE = {'hero-session.webp':(.86,.96,2), 'community.webp':(.91,.97,1), 'festival.webp':(.82,.96,0), 'outdoor-community.webp':(.93,.98,2), 'street-performance.webp':(.88,.98,2)}

def process(root=Path('assets'), report_path=Path('privacy-review.json')):
    report=[]
    for name,(reference,expected,crop,boxes) in SPECS.items():
        p=root/name
        before=hashlib.sha256(p.read_bytes()).hexdigest()
        if before != expected: raise ValueError(f'Unreviewed source: {name}')
        with Image.open(p) as source: im=source.convert('RGB')
        sx,sy=im.width/reference[0],im.height/reference[1]
        def scale(box): return tuple(round(v*(sx if i%2==0 else sy)) for i,v in enumerate(box))
        for rect in boxes:
            x0,y0,x1,y1=scale(rect); w,h=x1-x0,y1-y0; d=min(w,h)
            pad=max(4,round(d*.26)); outer=max(pad+2,round(d*.52)); feather=max(2,d*.13)
            region=(max(0,x0-outer),max(0,y0-outer),min(im.width,x1+outer),min(im.height,y1+outer))
            patch=im.crop(region); mask=Image.new('L',patch.size)
            ImageDraw.Draw(mask).ellipse((x0-region[0]-pad//2,y0-region[1]-pad//2,x1-region[0]+pad//2,y1-region[1]+pad//2),fill=255)
            core=mask.filter(ImageFilter.GaussianBlur(max(2,pad/3)))
            halo=Image.new('L',patch.size)
            ImageDraw.Draw(halo).ellipse((x0-region[0]-pad,y0-region[1]-pad,x1-region[0]+pad,y1-region[1]+pad),fill=210)
            halo=halo.filter(ImageFilter.GaussianBlur(feather))
            mask=ImageChops.lighter(core,halo)
            im.paste(patch.filter(ImageFilter.GaussianBlur(max(5,d*.22))),region,mask)
        if crop: im=im.crop(scale(crop))
        sat,contrast,warmth=GRADE[name]
        im=ImageEnhance.Color(im).enhance(sat)
        im=ImageEnhance.Contrast(im).enhance(contrast)
        # Soft lifted blacks, gently rolled highlights, restrained warmth.
        lut=[max(0,min(255,round(4+v*.97+shift*(1-v/255)))) for shift in (warmth,0,-warmth) for v in range(256)]
        im=im.point(lut)
        im.save(p,'WEBP',quality=84,method=6)
        report.append(dict(file=name,regions=len(boxes),source_sha256=before,derivative_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=list(im.size),grade=list(GRADE[name]),review='manual_candidate_v3'))
    report_path.write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=='__main__': process()
