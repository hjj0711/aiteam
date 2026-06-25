"""
NEWWORLD-CHAT-018 QA — Web/H5 Playwright tests
Tests: viewport lock, text contrast, guest login flow
"""
import json, os, sys
from datetime import datetime
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = "/Users/kit/Documents/myself/aiteam/tasks/screenshots"
BASE_URL = "http://localhost:5173"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = []
screenshots = []

def record(tid, check, passed, detail=""):
    s = "PASS" if passed else "FAIL"
    results.append((tid, check, s, detail))
    print(f"  [{s}] #{tid} {check} -- {detail}")

def ss(page, name):
    p = os.path.join(SCREENSHOT_DIR, name)
    page.screenshot(path=p, full_page=False)
    screenshots.append((name, p))
    print(f"  [SCREENSHOT] {p}")

def test_viewport(label, w, h):
    print(f"\n{'='*60}\nTesting {label} ({w}x{h})\n{'='*60}")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=2 if w < 500 else 1)
        page = ctx.new_page()

        api_reqs = []
        api_resps = []
        page.on("request", lambda r: api_reqs.append({"url": r.url, "method": r.method}) if "/auth/guest" in r.url else None)
        page.on("response", lambda r: api_resps.append({"url": r.url, "status": r.status, "body": (lambda b: r.json() if r.ok else None)(None)}) if "/auth/guest" in r.url else None)

        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)

        # Overflow
        hsw = page.evaluate("document.documentElement.scrollWidth")
        iw = page.evaluate("window.innerWidth")
        bsw = page.evaluate("document.body.scrollWidth")
        record(1, f"{label}: html scrollWidth<=innerWidth", hsw <= iw, f"scrollWidth={hsw} innerWidth={iw}")
        record(2, f"{label}: body scrollWidth<=innerWidth", bsw <= iw, f"scrollWidth={bsw} innerWidth={iw}")
        has_h = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        record(3, f"{label}: no h-scrollbar", not has_h, f"h_scrollbar={has_h}")

        # Title
        title = page.locator("ion-title")
        if title.count() > 0:
            tt = title.first.inner_text()
            record(4, f"{label}: ion-title visible", bool(tt.strip()), f"text='{tt}'")
        else:
            record(4, f"{label}: ion-title visible", False, "no ion-title")

        # Labels
        body_txt = page.inner_text("body")
        record(5, f"{label}: form labels visible", "邮箱" in body_txt and "游客登录" in body_txt,
               f"邮箱={'Y' if '邮箱' in body_txt else 'N'} 游客={'Y' if '游客登录' in body_txt else 'N'}")

        # Input color
        ic = page.evaluate("""()=>{const e=document.querySelector('ion-input');if(!e)return null;const i=e.shadowRoot&&e.shadowRoot.querySelector('input');return i?getComputedStyle(i).color:getComputedStyle(e).color;}""")
        is_light = ic and "255" in str(ic)
        record(6, f"{label}: IonInput text visible", is_light, f"color={ic}")
        print(f"  [INFO] {label} body bg={page.evaluate('getComputedStyle(document.body).backgroundColor')}")

        ss(page, f"chat_app_qa3_{label}_01_login.png")

        # Guest button
        gb = page.locator("ion-button:has-text('游客登录')")
        if gb.count() == 0:
            gb = page.locator("button:has-text('游客登录')")
        has_btn = gb.count() > 0
        record(7, f"{label}: guest button found", has_btn, f"count={gb.count()}")

        if has_btn:
            vis = gb.first.is_visible()
            en = gb.first.is_enabled()
            record(8, f"{label}: guest button visible+enabled", vis and en, f"visible={vis} enabled={en}")

            gb.first.click()
            page.wait_for_timeout(4000)
            ss(page, f"chat_app_qa3_{label}_02_after_click.png")

            greq = [r for r in api_reqs if "/auth/guest" in r["url"]]
            gres = [r for r in api_resps if "/auth/guest" in r["url"]]

            if greq:
                record(9, f"{label}: POST /auth/guest sent", True, f"url={greq[0]['url']}")
            else:
                record(9, f"{label}: POST /auth/guest sent", False, "NO request captured")

            if gres:
                st = gres[0]["status"]
                record(10, f"{label}: /auth/guest response", st in (200,201), f"status={st}")
            else:
                record(10, f"{label}: /auth/guest response", False, "no response (CORS/backend)")

            curl = page.url
            on_rooms = "/rooms" in curl
            record(11, f"{label}: navigated to /rooms", on_rooms, f"url={curl}")

            if on_rooms:
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(1000)
                hsw2 = page.evaluate("document.documentElement.scrollWidth")
                bsw2 = page.evaluate("document.body.scrollWidth")
                iw2 = page.evaluate("window.innerWidth")
                record(12, f"{label}: rooms html overflow ok", hsw2 <= iw2, f"sw={hsw2} iw={iw2}")
                record(13, f"{label}: rooms body overflow ok", bsw2 <= iw2, f"sw={bsw2} iw={iw2}")
                record(14, f"{label}: rooms has content", len(page.inner_text("body")) > 5)
                ss(page, f"chat_app_qa3_{label}_03_rooms.png")
            else:
                bt = page.inner_text("body")
                record(12, f"{label}: error/feedback", len(bt) > 5, f"preview={bt[:200]}")
                record(13, f"{label}: rooms overflow", False, "skipped")
                record(14, f"{label}: rooms content", False, "skipped")
                ss(page, f"chat_app_qa3_{label}_03_error.png")
        else:
            ss(page, f"chat_app_qa3_{label}_02_no_button.png")
            for tid in range(8, 15):
                record(tid, f"{label}: (no button)", False, "skipped")

        browser.close()

# RUN
print("="*60)
print("NEWWORLD-CHAT-018 QA -- Playwright Web/H5")
print(f"Target: {BASE_URL}  Backend: https://malou.site/api")
print("="*60)

test_viewport("mobile", 390, 844)
test_viewport("desktop", 1280, 800)

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
p = sum(1 for _,_,s,_ in results if s=="PASS")
f = sum(1 for _,_,s,_ in results if s=="FAIL")
print(f"{p}/{len(results)} PASS, {f}/{len(results)} FAIL")
for tid, check, status, detail in results:
    if status == "FAIL":
        print(f"  [FAIL] #{tid} {check} -- {detail}")

rp = os.path.join(SCREENSHOT_DIR, "qa_report_v3.json")
with open(rp, "w") as fh:
    json.dump({"timestamp": datetime.now().isoformat(), "target": BASE_URL,
               "results": [{"id": r[0],"check":r[1],"status":r[2],"detail":r[3]} for r in results],
               "screenshots": [{"name":s[0],"path":s[1]} for s in screenshots],
               "summary": {"pass":p,"fail":f,"total":len(results)}}, fh, indent=2, ensure_ascii=False)
print(f"\nReport: {rp}")
sys.exit(0 if f == 0 else 1)
