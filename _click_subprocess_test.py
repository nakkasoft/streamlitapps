import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://localhost:8597", wait_until="networkidle", timeout=30000)
    btn = page.locator("button", has_text="서브프로세스 실행")
    btn.first.wait_for(state="visible", timeout=20000)
    print("button found:", btn.count())
    btn.first.click()
    for i in range(15):
        time.sleep(1)
        content = page.content()
        if "결과:" in content:
            print(f"[{i}s] rendered")
            break
        print(f"[{i}s] waiting...")
    browser.close()
    print("CLICK TEST DONE")
