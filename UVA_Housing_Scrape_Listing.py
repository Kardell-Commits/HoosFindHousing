from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

df=pd.read_csv("UVA_housing_results.csv")
driver= webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait= WebDriverWait(driver,10)

details=[]

for i, row in df.iterrows():
    print(f"Scraping{i+1}/{len(df)}: {row['title']}")
    try: 
        driver.get(row['link'])
        time.sleep(3)
        
        ## LEASE TERMS SCRAPING
        try: 
            lease=driver.find_elements(By.CSS_SELECTOR,"section[data-qaid='leaseTerms'] li.list-item")
            lease_terms = ", ".join([el.text.strip() for el in lease if el.text.strip()])
        except:
            lease_terms=""
        
        ## AMENITIES 
        try: 
            amenity=driver.find_elements(By.CSS_SELECTOR,"div[aria-labelledby='listing-amenities'] span.leading-tight")
            amenities=", ".join([el.text.strip() for el in amenity if el.text.strip()])
        except:
            amenities=""
            
        ##FLOOR PLAN OPTIONS 
        floor_plans= driver.find_elements(By.CSS_SELECTOR, "tr[data-qaid='floorPlanRow']")
        
        if floor_plans:
            for plan in floor_plans:
                try:
                    beds=plan.find_element(By.CSS_SELECTOR,"td[data-qaid='beds']").text.strip()
                except:
                    beds=""
                
                try:
                    baths = plan.find_element(By.CSS_SELECTOR, "td[data-qaid='baths']").text.strip()
                except:
                    baths=""
            
                try:
                    floor_plan_price = plan.find_element(By.CSS_SELECTOR, "td[data-qaid='price']").text.strip()
                except:
                    floor_plan_price=""
                    
                try:
                    sqrft = plan.find_element(By.CSS_SELECTOR, "td[data-qaid='sqFeet']").text.strip()
                except:
                    sqrft=""
                    
                try:
                    availability= plan.find_element(By.CSS_SELECTOR, "td[data-qaid='availability']").text.strip()
                except:
                    availability=""
                
                details.append({"title": row['title'], "address": row['address'],"distance": row['distance'],"link": row['link'],"beds": beds,"baths": baths,"price": floor_plan_price,"sqft": sqrft, "availability": availability, "lease_terms":lease_terms, "amenities":amenities})
        else:
            
                details.append({"title": row['title'], "address": row['address'],"distance": row['distance'],"link": row['link'],"beds": "","baths": "","price": row['price'],"sqft": "" ,"availability":"", "lease_terms":lease_terms, "amenities":amenities})
    except Exception as e:
        print(f"Error:{e}")
        details.append({
            "title": row['title'],
            "address": row['address'],
            "distance": row['distance'],
            "link": row['link'],
            "beds": "", "baths": "", "price": row['price'],
            "sqft": "", "availability": "",
            "lease_terms": "", "amenities": ""
        })
df_details=pd.DataFrame(details)
print(df_details)
df_details.to_csv("UVA_housing_detailed.csv",index=False)
driver.quit()
