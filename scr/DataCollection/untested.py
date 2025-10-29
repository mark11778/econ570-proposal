import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = Options()
options.add_argument('--headless')

service = Service(executable_path='/usr/bin/chromedriver')
driver = webdriver.Chrome(options=options, service=service)

try:
    year = "24"  # Last two digits of the year
    for precinct in range(1, 50):  # Loop through precinct codes 01 to 99
        precinct_code = f"{precinct:02}"  # Format to ensure two digits
        df = pd.DataFrame({
            'Date Issue': [],
            'Location': [],
            'Comment': [],
            'License Plate': [],
            'Type': [],
            'Type #': [],
            'Ticket #': []
            })
        
        for ticket_number in range(1, 100000):  # Ticket numbers from 00001 to 99999
            formatted_ticket_number = f"{ticket_number:05}"  # Format to ensure five digits
            full_ticket_number = f"{year}P{precinct_code}{formatted_ticket_number}"
            
            start_url = "https://parkingtickets.cityofmadison.com/tickets/"
            driver.get(start_url)

            input_element = driver.find_element(By.ID, "ticket_plate_vin")
            input_element.clear()
            input_element.send_keys(full_ticket_number)

            search_button = driver.find_element(By.ID, "search_ticket")
            search_button.click()

            wait = WebDriverWait(driver, 5)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#ticket_detail div.col-md-6")))

                ticket_info_div = driver.find_element(By.CSS_SELECTOR, "div#ticket_detail div.col-md-6")
                paragraphs = ticket_info_div.find_elements(By.TAG_NAME, "p")
                data = {}
                data['Ticket #'] = full_ticket_number
                for p in paragraphs:
                    try:
                        strong_tag = p.find_element(By.TAG_NAME, "strong").text
                        strong_following_text = p.text.replace(strong_tag, '').strip()

                        if 'Issue Date and Time:' in strong_tag:
                            data['Date Issue'] = strong_following_text
                        elif 'Location:' in strong_tag:
                            data['Location'] = strong_following_text
                        elif 'Comment:' in strong_tag:
                            data['Comment'] = strong_following_text
                    except Exception as e:
                        print(f"Error retrieving part of the data for {full_ticket_number}: {e}")

                try:
                    data['License Plate'] = driver.find_element(By.CSS_SELECTOR, "div.plate_number").text
                except Exception as e:
                    data['License Plate'] = "Not Found"
                    print(f"License Plate not found for {full_ticket_number}: {e}")

                try:
                    data['Type'] = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="violation_surcharge_table"]/tbody/tr[1]/th'))).text
                except Exception as e:
                    data['Type'] = "Not Found"
                    print(f"Violation Type not found for {full_ticket_number}: {e}")
                    
                data['Type #'] = data['Type #'][0:3]

                new_row = pd.DataFrame([data], columns=df.columns)
                df = pd.concat([df, new_row], ignore_index=True)

            except Exception as e:
                print(f"No more tickets found for {full_ticket_number}, error: {e}")
                if df.empty is False:
                    df.to_csv(f"parking_tickets_data_{precinct:02}.csv", index=False)
                else:
                    print("df was empty")

                break  # Break if no ticket detail page loaded, adjust as needed based on actual site behavior

finally:
    driver.quit()
    print("finished")
