from pathlib import Path
import hashlib, json
import cv2
import numpy as np
from PIL import Image

# Exact approved archive sources; crop only outdoor foreground.
SOURCES = {
    'hero-session.webp': ('190ddbb1d6cf8942c490f4d35ff458a418b42aacd7c992c978ccb277a567c717', None),
    'community.webp': ('bafe57c5942f8da9cf35d02f9e2338d8252c970f8ce704736948d704ca95acdc', None),
    'festival.webp': ('9ddc13f1df9aa2e1789b6003ca6f415cc3bced8766bd714e756e3a3956e4722b', None),
    'outdoor-community.webp': ('df22893337d674f973d3e2346031d82765bf94594ba1cac6ef06f27baf52bbe3', .768),
    'street-performance.webp': ('3cb7bfcc6dfc9dbe692eb206953ad1e2430a6e13613eb8a3964c92802ffa0614', None),
}
def process(root=Path('assets'), report=Path('privacy-review.json')):
    records=[]
    for name,(expected,crop) in SOURCES.items():
        p=root/name
        before=hashlib.sha256(p.read_bytes()).hexdigest()
        if before != expected: raise ValueError(f'Unreviewed source: {name}')
        with Image.open(p) as src: im=src.convert('RGB')
        if crop: im=im.crop((0,0,round(im.width*crop),im.height))
        a=np.asarray(im); h,w=a.shape[:2]
        # Whole-frame colour simplification; no local face masks or synthetic figures.
        scale=min(1,(480 if name=="hero-session.webp" else 300)/max(h,w)); size=(max(1,round(w*scale)),max(1,round(h*scale)))
        small=cv2.resize(a,size,interpolation=cv2.INTER_AREA)
        wash=cv2.bilateralFilter(small,9,55,8)
        wash=cv2.bilateralFilter(wash,7,45,5)
        wash=cv2.resize(wash,(w,h),interpolation=cv2.INTER_CUBIC).astype(np.float32)
        # Muted pigments, warm paper, fine deterministic grain; no dark outline.
        light=wash.mean(axis=2,keepdims=True)
        wash=light+(wash-light)*.88
        rng=np.random.default_rng(27)
        grain=rng.normal(0,1.8,(h,w,1)).astype(np.float32)
        result=wash*.91+np.array([250,242,224],np.float32)*.09+grain
        Image.fromarray(np.clip(result,0,255).astype(np.uint8)).save(p,'WEBP',quality=83,method=6)
        records.append(dict(file=name,source_sha256=before,derivative_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=[w,h],review='watercolor_candidate_manual_review_required',anonymization_guaranteed=False))
    report.write_text(json.dumps(records,indent=2)); print(json.dumps(records))
if __name__=='__main__': process()
