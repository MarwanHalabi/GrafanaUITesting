import os
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import tempfile
import shutil
import time

GRAFANA_URL = os.environ.get('GRAFANA_URL', 'http://localhost:3000')


class GrafanaUITest(unittest.TestCase):
    def setUp(self):
        self._user_data_dir = tempfile.mkdtemp()
        options = Options()
        if os.environ.get('HEADLESS', '1') == '1':
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f'--user-data-dir={self._user_data_dir}')
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(GRAFANA_URL)

    def tearDown(self):
        self.driver.quit()
        shutil.rmtree(self._user_data_dir, ignore_errors=True)

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

        # FINAL ASSERT: element must exist
        target = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='_r2c_']"))
        )
        self.assertIsNotNone(target, "Element //*[@id='_r2c_'] should be present at the end")


        # time.sleep(222)   

if __name__ == '__main__':
    unittest.main()
