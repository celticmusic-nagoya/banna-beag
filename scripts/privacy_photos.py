from pathlib import Path
import cv2
import json
import hashlib
from PIL import Image, ImageFilter
detectors = [(cv2.CascadeClassifier(cv2.data.haarcascades + n), flip) for n, flip in [('haarcascade_frontalface_default.xml', False), ('haarcascade_profileface.xml', False), ('haarcascade_profileface.xml', True)]]
assert all(not d.empty() for d, _ in detectors)
report = []
for p in sorted(Path('assets').glob('*.webp')):
    before = hashlib.sha256(p.read_bytes()).hexdigest()
    with Image.open(p) as source:
        im = source.convert('RGB')
    gray = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2GRAY)
    boxes = []
    for detector, flip in detectors:
        g = cv2.flip(gray, 1) if flip else gray
        for x,y,w,h in detector.detectMultiScale(g, scaleFactor=1.08, minNeighbors=4, minSize=(18,18)):
            if flip: x = im.width-x-w
            box = (max(0,int(x-w*.18)),max(0,int(y-h*.22)),min(im.width,int(x+w*1.18)),min(im.height,int(y+h*1.22)))
            if box not in boxes: boxes.append(box)
    for box in boxes:
        region = im.crop(box)
        im.paste(region.filter(ImageFilter.GaussianBlur(max(4,region.width/7))),box)
    if boxes: im.save(p,'WEBP',quality=88,method=6)
    report.append(dict(file=p.name, detected=len(boxes), boxes=boxes, original_sha256=before, derivative_sha256=hashlib.sha256(p.read_bytes()).hexdigest(), review='manual_required'))
Path('privacy-review.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
