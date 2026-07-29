import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://localhost:8502", wait_until="networkidle", timeout=30000)
    btn = page.locator("button", has_text="빈자리 조회")
    btn.first.wait_for(state="visible", timeout=20000)
    print("button found:", btn.count())
    btn.first.click()
    for i in range(60):
        time.sleep(2)
        content = page.content()
        if "예약가능" in content or "조회 결과가 없습니다" in content:
            print(f"[{i*2}s] rendered")
            break
        print(f"[{i*2}s] waiting...")
    browser.close()
    print("CLICK TEST DONE")
