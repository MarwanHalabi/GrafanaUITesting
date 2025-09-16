# tests/test_example.py
import os, re, time, uuid, unittest, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse

# Config
GRAFANA_URL  = os.getenv("GRAFANA_URL", "http://54.195.151.217:3000")
API_BASE_URL = os.getenv("API_BASE_URL", GRAFANA_URL)  # reuse unless you proxy API
GRAFANA_USER = os.getenv("GRAFANA_USER", "admin")
GRAFANA_PASS = os.getenv("GRAFANA_PASS", "admin")
API_TOKEN    = os.getenv("GRAFANA_API_TOKEN")  # optional: if set, use Bearer token

HEADLESS = os.getenv("HEADLESS", "0").lower() in ("1", "true")
IN_CI    = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"

class GrafanaUITest(unittest.TestCase):
    def setUp(self):
        opts = Options()
        if HEADLESS: opts.add_argument("--headless=new")
        if IN_CI:
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-gpu")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")
        self.driver = webdriver.Chrome(options=opts)
        self.driver.set_page_load_timeout(60)
        self.driver.get(GRAFANA_URL)
        self.dashboard_uid = None  # will be set after save

    def tearDown(self):
        try: self.driver.quit()
        except Exception: pass

    # --- helpers ---

    def _extract_uid_from_url(self, url: str) -> str:
        path = urlparse(url).path  # e.g. /d/719a.../ui-test-xxxx
        parts = [p for p in path.split("/") if p]
        if "d" in parts:
            i = parts.index("d")
            if i + 1 < len(parts) and parts[i+1]:
                return parts[i+1]
        m = re.search(r"/d/([^/?#]+)", url)
        if m:
            return m.group(1)
        raise AssertionError(f"Could not extract UID from URL: {url}")

    def _get_dashboard_via_api(self, uid: str) -> dict:
        url = f"{API_BASE_URL}/api/dashboards/uid/{uid}"
        headers, auth = {}, None
        if API_TOKEN:
            headers["Authorization"] = f"Bearer {API_TOKEN}"
        else:
            auth = (GRAFANA_USER, GRAFANA_PASS)
        r = requests.get(url, headers=headers, auth=auth, timeout=15)
        self.assertEqual(r.status_code, 200, f"API GET failed: {r.status_code} {r.text}")
        return r.json()

    def _read_uid_from_breadcrumb(self, d, dashboard_name: str, timeout: int = 30) -> str:
        """
        Reads the dashboard UID from the breadcrumb <a> href after save.
        Prefers the crumb whose title == dashboard_name; falls back to last crumb.
        """
        # Prefer exact-title crumb (stable)
        try:
            crumb = WebDriverWait(d, timeout).until(EC.visibility_of_element_located((
                By.XPATH,
                f"//nav//a[contains(@data-testid,'breadcrumb') and @title=normalize-space('{dashboard_name}')]"
            )))
        except Exception:
            # Fallback: last breadcrumb link
            crumb = WebDriverWait(d, timeout).until(EC.visibility_of_element_located((
                By.CSS_SELECTOR, "nav ol li:last-child a[data-testid*='breadcrumb']"
            )))
        href = crumb.get_attribute("href")
        return self._extract_uid_from_url(href)

    def test_grafana_new_visualization_flow(self):
        d = self.driver

        # Login
        WebDriverWait(d, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='data-testid Username input field']"))
        )
        d.find_element(By.CSS_SELECTOR, "[data-testid='data-testid Username input field']").send_keys(GRAFANA_USER)
        d.find_element(By.CSS_SELECTOR, "[data-testid='data-testid Password input field']").send_keys(GRAFANA_PASS)
        d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # Skip onboarding (best-effort)
        try:
            WebDriverWait(d, 6).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Skip']"))
            ).click()
        except Exception:
            pass

        # Welcome check
        header = WebDriverWait(d, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[text()='Welcome to Grafana']"))
        )
        self.assertEqual(header.text, "Welcome to Grafana")

        # New dashboard
        WebDriverWait(d, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="New"]'))).click()
        WebDriverWait(d, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='New dashboard']"))).click()

        # Add visualization
        WebDriverWait(d, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="data-testid Create new panel button"]'))
        ).click()

        # Select built-in Grafana source (3rd button in built-in list)
        buttons = WebDriverWait(d, 10).until(EC.presence_of_all_elements_located((
            By.XPATH, "//div[@data-testid='data-testid Built in data source list']//button"
        )))
        grafana_button = buttons[2]
        d.execute_script("arguments[0].scrollIntoView(true);", grafana_button)
        d.execute_script("arguments[0].click();", grafana_button)

        # Save dashboard (top bar)
        save_btn = WebDriverWait(d, 10).until(EC.element_to_be_clickable((
            By.XPATH, "//button[@data-testid='data-testid Save dashboard button']"
        )))
        d.execute_script("arguments[0].click()", save_btn)

        # Name it in the drawer
        dashboard_name = f"UI Test {uuid.uuid4().hex[:6]}"
        title_input = WebDriverWait(d, 10).until(EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "div[role='dialog'] input[data-testid='Save dashboard title field'], "
            "div[role='dialog'] input[aria-label='Save dashboard title field'], "
            "div[role='dialog'] input[name='title']"
        )))
        title_input.click(); title_input.clear(); title_input.send_keys(dashboard_name)

        save_btn = WebDriverWait(d, 10).until(EC.element_to_be_clickable((
            By.XPATH, "//button[@data-testid='data-testid Save dashboard drawer button']"
        )))
        d.execute_script("arguments[0].click();", save_btn)

        # --- Capture UID from breadcrumb (robust, does not rely on current_url) ---
        self.dashboard_uid = self._read_uid_from_breadcrumb(d, dashboard_name, timeout=30)

        # Backend assert: persisted via REST API
        time.sleep(1.0) # buffer for backend to process the save
        data = self._get_dashboard_via_api(self.dashboard_uid)
        api_title = data.get("dashboard", {}).get("title")
        self.assertEqual(api_title, dashboard_name, f"API title mismatch: {api_title} != {dashboard_name}")
        self.assertEqual(data.get("dashboard", {}).get("uid"), self.dashboard_uid)
        self.assertGreaterEqual(data.get("dashboard", {}).get("version", 1), 1)

if __name__ == "__main__":
    unittest.main()
