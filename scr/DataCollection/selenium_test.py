from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


options = Options()
options.add_argument('--headless')

service = Service(executable_path='/usr/bin/chromedriver')

driver = webdriver.Chrome(options, service)

driver.get("https://www.google.com")
print(driver.title)
driver.quit()
