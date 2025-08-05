import os
import unittest
from selenium import webdriver

GRAFANA_URL = os.environ.get('GRAFANA_URL', 'http://localhost:3000')  # Default to localhost if not set

class ExampleTestCase(unittest.TestCase):
    
    
    def setUp(self):
        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.quit()

    def test_page_title(self):
        self.driver.get(GRAFANA_URL)
        self.assertIn('Grafana UI', self.driver.title)

if __name__ == '__main__':
    unittest.main() 