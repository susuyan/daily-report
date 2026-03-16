from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    
    # 先执行数据采集脚本生成最新数据
    import subprocess
    subprocess.run(['python3', 'scripts/fetch_data.py'], cwd='/Users/admin/.openclaw/workspace/daily-report')
    
    page.goto('http://localhost:8080/site/')
    time.sleep(3)  # 等待数据加载
    
    # 截图桌面端
    page.screenshot(path='/Users/admin/.openclaw/workspace/daily-report/preview-desktop.png', full_page=True)
    
    # 截图移动端
    page.set_viewport_size({'width': 375, 'height': 812})
    time.sleep(1)
    page.screenshot(path='/Users/admin/.openclaw/workspace/daily-report/preview-mobile.png', full_page=True)
    
    browser.close()
    print("Screenshots saved!")
