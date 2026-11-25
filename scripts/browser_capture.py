import asyncio, json, hashlib
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image, ImageStat, ImageFilter
OUT=Path("capture-review")
OUT.mkdir(exist_ok=True)
URL="https://www.instagram.com/reel/DbLmBXBSG2e/"
async def main():
    report={"source":URL,"status":"BLOCKED","frames":[]}
    try:
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=False)
            page=await browser.new_page(viewport={"width":1920,"height":1080})
            await page.goto(URL,wait_until="domcontentloaded",timeout=45000)
            video=page.locator("video:visible").first
            await video.wait_for(timeout=20000)
            await video.click(timeout=5000)
            previous=-1
            for i in range(16):
                await page.wait_for_timeout(1500)
                state=await video.evaluate("(v)=>({time:v.currentTime,paused:v.paused,ready:v.readyState,width:v.videoWidth,height:v.videoHeight})")
                if state["paused"] or state["ready"]<2 or state["time"]<=previous or not state["width"]: continue
                previous=state["time"]
                path=OUT/f"frame-{i:02}.png"
                await video.screenshot(path=str(path),timeout=5000)
                with Image.open(path) as im:
                    gray=im.convert("L").resize((128,128))
                    stat=ImageStat.Stat(gray)
                    if stat.mean[0]<12 or stat.stddev[0]<8:
                        path.unlink(); continue
                    digest=hashlib.sha256(path.read_bytes()).hexdigest()
                    if any(x["sha256"]==digest for x in report["frames"]):
                        path.unlink(); continue
                    report["frames"].append({"file":path.name,"second":state["time"],"sha256":digest,"edge_stddev":ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).stddev[0]})
            await browser.close()
        if len(report["frames"])>=2: report["status"]="FRAMES_READY_FOR_PRIVATE_REVIEW"
    except Exception as e:
        report["error_type"]=type(e).__name__
    finally:
        (OUT/"manifest.json").write_text(json.dumps(report,indent=2))
        print(json.dumps({"status":report["status"],"count":len(report["frames"])}))
    if report["status"]=="BLOCKED": raise SystemExit(1)
asyncio.run(main())
