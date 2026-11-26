from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1440,900')

try:
    driver = webdriver.Chrome(options=options)
    driver.get('http://localhost:8088/index.html')
    time.sleep(2)
    
    # 1. Desktop 1440x900 viewport
    sw_desk = driver.execute_script('return document.documentElement.scrollWidth')
    iw_desk = driver.execute_script('return window.innerWidth')
    print(f'Desktop 1440x900: window={iw_desk}, scrollWidth={sw_desk}, diff={sw_desk - iw_desk}')
    
    # Check JS console logs
    logs = driver.get_log('browser')
    print(f'Browser console logs count: {len(logs)}')
    for log in logs:
        if log['level'] == 'SEVERE':
            print('CONSOLE ERROR:', log['message'])

    # 2. Mobile 390x844 viewport
    driver.set_window_size(390, 844)
    time.sleep(1)
    sw_mob = driver.execute_script('return document.documentElement.scrollWidth')
    iw_mob = driver.execute_script('return window.innerWidth')
    print(f'Mobile 390x844: window={iw_mob}, scrollWidth={sw_mob}, diff={sw_mob - iw_mob}')
    
    # Check key elements in mobile
    has_hero = driver.execute_script('return document.querySelector(".hero-title") !== null')
    has_demo = driver.execute_script('return document.querySelector("#demo-canvas") !== null')
    print(f'DOM elements check: hero_title={has_hero}, demo_canvas={has_demo}')

    # Take screenshot for visual verification
    driver.set_window_size(1440, 900)
    driver.save_screenshot('results/landing_desktop_1440.png')
    driver.set_window_size(390, 844)
    driver.save_screenshot('results/landing_mobile_390.png')

    driver.quit()
    print('Visual screenshots and layout tests completed successfully!')
except Exception as e:
    print('Selenium exception:', e)
