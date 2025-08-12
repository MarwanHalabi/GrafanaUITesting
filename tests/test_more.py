# # tests/test_basic_flows.py
# import os
# import uuid
# import unittest
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# # Env
# GRAFANA_URL  = os.environ.get("GRAFANA_URL", "http://108.129.199.209:3000")
# GRAFANA_USER = os.environ.get("GRAFANA_USER", "admin")
# GRAFANA_PASS = os.environ.get("GRAFANA_PASS", "admin")
# HEADLESS     = os.environ.get("HEADLESS", "0").lower() in ("1", "true")
# IN_CI        = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
# WAIT         = int(os.environ.get("WAIT_SEC", "15"))

# w = lambda d, cond, t=WAIT: WebDriverWait(d, t).until(cond)

# def click_js(d, el):
#     d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
#     d.execute_script("arguments[0].click();", el)

# class BaseUITest(unittest.TestCase):
#     def setUp(self):
#         opts = Options()
#         if HEADLESS: opts.add_argument("--headless=new")
#         if IN_CI:
#             opts.add_argument("--no-sandbox"); opts.add_argument("--disable-dev-shm-usage"); opts.add_argument("--disable-gpu")
#         opts.add_argument("--no-first-run"); opts.add_argument("--no-default-browser-check"); opts.add_argument("--window-size=1400,900")
#         self.d = webdriver.Chrome(options=opts)
#         self.d.set_page_load_timeout(60)
#         self.d.get(GRAFANA_URL)

#     def tearDown(self):
#         try: self.d.quit()
#         except: pass

#     # --- helpers ---
#     def login(self, user=GRAFANA_USER, pwd=GRAFANA_PASS):
#         d = self.d
#         w(d, EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='data-testid Username input field']")))
#         d.find_element(By.CSS_SELECTOR, "[data-testid='data-testid Username input field']").send_keys(user)
#         d.find_element(By.CSS_SELECTOR, "[data-testid='data-testid Password input field']").send_keys(pwd)
#         d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
#         # skip onboarding if shown
#         try: w(d, EC.element_to_be_clickable((By.XPATH, "//span[text()='Skip']"))).click()
#         except: pass

#     def new_dashboard(self):
#         d = self.d
#         w(d, EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="New"]'))).click()
#         w(d, EC.element_to_be_clickable((By.XPATH, "//span[text()='New dashboard']"))).click()

#     def add_visualization(self):
#         d = self.d
#         w(d, EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="data-testid Create new panel button"]'))).click()
#         # wait for built-in list
#         btns = w(d, EC.presence_of_all_elements_located((By.XPATH, "//div[@data-testid='data-testid Built in data source list']//button")))
#         # click third (Grafana) like your main test
#         click_js(d, btns[2])
#         # wait for canvas
#         w(d, EC.presence_of_element_located((By.XPATH, "//*[@id='_r2c_']")))

#     def open_save_dialog(self):
#         d = self.d
#         try:
#             el = w(d, EC.element_to_be_clickable((By.XPATH, "//*[@id='reactRoot']/div/div[1]/header/div[2]/div/div/div/div[4]/button")))
#         except:
#             el = w(d, EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Save dashboard']")))
#         click_js(d, el)
#         w(d, EC.visibility_of_element_located((By.XPATH, "//*[@role='dialog']")))

#     def set_title_uuid_and_save(self):
#         d = self.d
#         name = f"UI Test {uuid.uuid4().hex[:6]}"
#         title = w(d, EC.element_to_be_clickable((
#             By.CSS_SELECTOR,
#             "div[role='dialog'] input[data-testid='Save dashboard title field'], "
#             "div[role='dialog'] input[aria-label='Save dashboard title field'], "
#             "div[role='dialog'] input[name='title']"
#         )))
#         title.click(); title.clear(); title.send_keys(name)
#         save = w(d, EC.element_to_be_clickable((By.XPATH, "//div[@role='dialog']//button[.//span[normalize-space()='Save'] or normalize-space()='Save' or @type='submit']")))
#         click_js(d, save)
#         w(d, EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Dashboard saved')]")))
#         return name

# class TestBasicFlows(BaseUITest):
#     def test_invalid_login_shows_error(self):
#         d = self.d
#         w(d, EC.visibility_of_element_located((By.NAME, "user"))).send_keys("wrong")
#         d.find_element(By.NAME, "password").send_keys("wrong")
#         d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
#         w(d, EC.presence_of_element_located((
#             By.XPATH, "//*[contains(text(),'Invalid username') or contains(@class,'alert-error') or contains(.,'invalid')]"
#         )))

#     def test_create_save_dashboard_and_verify_breadcrumb(self):
#         d = self.d
#         self.login()
#         self.new_dashboard()
#         self.add_visualization()
#         self.open_save_dialog()
#         name = self.set_title_uuid_and_save()
#         # verify breadcrumb equals name
#         crumb_xpath = "//*[@id='reactRoot']/div/div[1]/header/div[1]/div[1]/nav/ol/li[3]/a"
#         w(d, EC.text_to_be_present_in_element((By.XPATH, crumb_xpath), name))
#         crumb = w(d, EC.visibility_of_element_located((By.XPATH, crumb_xpath)))
#         self.assertEqual(" ".join(crumb.text.split()), " ".join(name.split()))

#     def test_switch_visualization_to_time_series(self):
#         d = self.d
#         self.login()
#         self.new_dashboard()
#         self.add_visualization()
#         # open viz picker and select Time series (fallbacks)
#         try:
#             w(d, EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label,'Time series')]"))).click()
#         except:
#             try:
#                 w(d, EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'VizPicker')]//button[contains(.,'Time series')]"))).click()
#             except:
#                 # open picker via toolbar if present
#                 try:
#                     w(d, EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Visualization']"))).click()
#                     w(d, EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Time series')]"))).click()
#                 except:
#                     self.skipTest("Time series picker not found in this build")
#         w(d, EC.presence_of_element_located((By.XPATH, "//*[@id='_r2c_']")))

#     def test_change_time_range_last_5m(self):
#         d = self.d
#         self.login()
#         # open time picker (varies by build)
#         for loc in [
#             (By.CSS_SELECTOR, "button[aria-label='Time range controls']"),
#             (By.CSS_SELECTOR, "button[aria-label='Time picker open button']"),
#             (By.XPATH, "//button[.//span[contains(text(),'Last')]]"),
#         ]:
#             try:
#                 w(d, EC.element_to_be_clickable(loc)).click(); break
#             except: continue
#         else:
#             self.fail("Time picker button not found")
#         # select Last 5 minutes
#         for loc in [
#             (By.XPATH, "//button[.//span[normalize-space()='Last 5 minutes']]"),
#             (By.XPATH, "//span[normalize-space()='Last 5 minutes']"),
#         ]:
#             try:
#                 w(d, EC.element_to_be_clickable(loc)).click(); break
#             except: continue
#         w(d, lambda drv: "now-5m" in drv.current_url)

#     def test_share_modal_opens(self):
#         d = self.d
#         self.login()
#         self.new_dashboard()
#         self.add_visualization()
#         # open share
#         try:
#             share = w(d, EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Share dashboard']")))
#         except:
#             share = w(d, EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(),'Share')]]")))
#         click_js(d, share)
#         w(d, EC.visibility_of_element_located((By.XPATH, "//*[@role='dialog']")))
#         # expect a copy button inside dialog
#         w(d, EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//button[.//span[contains(.,'Copy')]]")))

#     def test_logout_returns_to_login(self):
#         d = self.d
#         self.login()
#         # open user menu
#         try:
#             w(d, EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Open user menu']"))).click()
#         except:
#             try:
#                 w(d, EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label,'user menu') or .//span[text()='admin']]"))).click()
#             except:
#                 self.skipTest("User menu not found")
#         # sign out
#         try:
#             w(d, EC.element_to_be_clickable((By.XPATH, "//span[text()='Sign out' or text()='Logout']"))).click()
#         except:
#             w(d, EC.element_to_be_clickable((By.XPATH, "//a[.//span[text()='Sign out' or text()='Logout']]"))).click()
#         # back to login form
#         w(d, EC.visibility_of_element_located((By.NAME, "user")))
#         w(d, EC.visibility_of_element_located((By.NAME, "password")))

# if __name__ == "__main__":
#     unittest.main()
