import pandas as pd
import os 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

options = Options()
options.add_argument('--headless')

service = Service(executable_path='/usr/bin/chromedriver')
driver = webdriver.Chrome(options=options, service=service)

try:
    year = "24"  
    for precinct in range(1, 32):  
        precinct_code = f"{precinct:02}"  
        if precinct == 21:
            continue
        df = pd.read_csv(f"../CollectedData/parking_tickets_data_{precinct_code}.csv")

        lastFound = df['Ticket #'].max()
        lastNum = int(lastFound[5:]) + 1


        for ticket_number in range(lastNum, 100000):  # Ticket numbers from 00001 to 99999
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
                            print(pd.to_datetime(strong_following_text))
                            data['Date Issue'] = pd.to_datetime(strong_following_text)
                        elif 'Location:' in strong_tag:
                            data['Location'] = strong_following_text
                    except Exception as e:
                        print(f"Error retrieving part of the data for {full_ticket_number}: {e}")

                try:
                        type_element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="violation_surcharge_table"]/tbody/tr[1]/th')))
                        violation_type = type_element.text.split(" ")[0]
                        
                        # Update the 'Type' in `data` dictionary based on conditions
                        if violation_type in ['005', '007']:
                            data['Type'] = "Parking"
                        elif violation_type == '009':
                            data['Type'] = "Meter"
                        else:
                            data['Type'] = violation_type
                except Exception as e:
                    data['Type'] = "Not Found"
                    print(f"Violation Type not found for {full_ticket_number}: {e}")

                try:
                    data["Hour"] = data['Date Issue'].hour
                    data["Day"] = data['Date Issue'].day_name()
                except Exception as e:
                    print(f"Error processing Date Issue for {full_ticket_number}: {e}")
                    continue


                new_row = pd.DataFrame([data], columns=df.columns)
                df = pd.concat([df, new_row], ignore_index=True)

            except Exception as e:
                if df.empty is False:
                    df.to_csv(f"../CollectedData/parking_tickets_data_{precinct:02}.csv", index=False)
                else:
                    print("df was empty")

                break  # Break if no ticket detail page loaded, adjust as needed based on actual site behavior

finally:
    driver.quit()
    print("finished")
