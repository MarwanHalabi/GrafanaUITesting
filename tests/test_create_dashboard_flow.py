# tests/test_example.py
import os
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import uuid

# Config
GRAFANA_URL = os.environ.get("GRAFANA_URL", "http://54.154.221.226:3000")
HEADLESS = os.environ.get("HEADLESS", "0").lower() in ("1", "true")
IN_CI = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"

class GrafanaUITest(unittest.TestCase):
    def setUp(self):
        opts = Options()
        if HEADLESS:
            opts.add_argument("--headless=new")
        if IN_CI:
            # CI hardening flags (don’t add locally so a window opens cleanly)
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-gpu")
        # Harmless everywhere
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")

        self.driver = webdriver.Chrome(options=opts)
        self.driver.set_page_load_timeout(60)
        self.driver.get(GRAFANA_URL)

    def tearDown(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    def test_grafana_new_visualization_flow(self):
        driver = self.driver

        # Login
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='data-testid Username input field']"))
        )
        driver.find_element(By.CSS_SELECTOR, "[data-testid='data-testid Username input field']").send_keys("admin")
        driver.find_element(By.CSS_SELECTOR, "[data-testid='data-testid Password input field']").send_keys("admin")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # Skip onboarding
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Skip']"))
        ).click()

        # Verify welcome message
        header = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[text()='Welcome to Grafana']"))
        )
        self.assertEqual(header.text, "Welcome to Grafana")

        # Click "+" (New) button in the toolbar
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="New"]'))
        ).click()

        # Click "New dashboard" in the dropdown
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='New dashboard']"))
        ).click()

        # Click "Add visualization" (Create new panel button)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="data-testid Create new panel button"]'))
        ).click()

        # Wait for all data source buttons to load
        buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((
                By.XPATH,
                "//div[@data-testid='data-testid Built in data source list']//button"
            ))
        )

        # Scroll and click the third button (-- Grafana --)
        grafana_button = buttons[2]
        driver.execute_script("arguments[0].scrollIntoView(true);", grafana_button)
        driver.execute_script("arguments[0].click();", grafana_button)
        
        # Open "Save dashboard" dialog
        save_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='reactRoot']/div/div[1]/header/div[2]/div/div/div/div[4]/button"))
        )
        driver.execute_script("arguments[0].click()", save_btn)  # JS click avoids overlay issues
        
        # Title input (based on your element)
        dashboard_name = f"UI Test {uuid.uuid4().hex[:6]}"
        title_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "div[role='dialog'] input[data-testid='Save dashboard title field'], "
                "div[role='dialog'] input[aria-label='Save dashboard title field'], "
                "div[role='dialog'] input[name='title']"
            ))
        )
        title_input.click()
        title_input.clear()
        title_input.send_keys(dashboard_name)

        # Confirm Save (dialog-scoped)
        save_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[@role='dialog']//button[.//span[normalize-space()='Save'] or normalize-space()='Save' or @type='submit']"
            ))
        )
        driver.execute_script("arguments[0].click();", save_btn)

        # Verify breadcrumb shows the saved dashboard name
        crumb_xpath = "//*[@id='reactRoot']/div/div[1]/header/div[1]/div[1]/nav/ol/li[3]/a"

        # wait until the breadcrumb contains the expected name
        WebDriverWait(driver, 15).until(
            EC.text_to_be_present_in_element((By.XPATH, crumb_xpath), dashboard_name)
        )

        # assert exact equality (normalize whitespace just in case)
        crumb = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, crumb_xpath))
        )
        actual_name = " ".join(crumb.text.split())
        expected_name = " ".join(dashboard_name.split())
        self.assertEqual(actual_name, expected_name, f"Dashboard name mismatch: expected '{expected_name}', got '{actual_name}'")
        time.sleep(10)

if __name__ == "__main__":
    unittest.main()
