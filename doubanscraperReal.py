import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# === SETUP ===
# Add as many movies as you want here
titles = {
'Aquaman': '3878007',
'Avatar: The Way of Water': '4811774', 
'Avengers: Age of Ultron': '10741834', 
'Avengers: Endgame': '26100958',
'Avengers: Infinity War': '24773958',
'Everything Everywhere All at Once': '30314848',
'Fast & Furious Presents: Hobbs & Shaw': '27163278', 
'Furious 7': '23761370',
'Jurassic World': '10440138', 
'Jurassic World: Fallen Kingdom': '26416062', 
'Ready Player One': '4920389',
'Spider-Man: Far From Home': '26931786', 
'The Fate of the Furious': '26260853',
'Transformers: Age of Extinction': '7054604',
'Transformers: The Last Knight': '25824686', 
'Venom': '3168101',
'Warcraft': '2131940', 
'Zootopia': '25662329',
}
output_folder = "output1"
os.makedirs(output_folder, exist_ok=True)

# Set up Chrome driver
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
# Add these options to improve reliability
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = webdriver.Chrome(options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
wait = WebDriverWait(driver, 15)  # Increased timeout

# Prompt user to log in
driver.get("https://www.douban.com/")
input("Please log into Douban manually in the browser window. Press Enter here when done...")

def scrape_movie_reviews(title, movie_id):
    all_reviews = []

    for rating in [1, 2]:
        start = 0
        while True:
            url = f"https://movie.douban.com/subject/{movie_id}/reviews?sort=hotest&rating={rating}&start={start}"
            print(f"📄 Loading page: {url}")
            driver.get(url)
            time.sleep(3)  # Increased wait time

            # Find all review divs
            review_divs = driver.find_elements(By.CSS_SELECTOR, "div.main.review-item")
            if not review_divs:
                print(f"No more reviews found for rating {rating}")
                break

            print(f"Found {len(review_divs)} reviews on this page")

            for i, review_div in enumerate(review_divs):
                try:
                    review_id = review_div.get_attribute("id")
                    print(f"Processing review {i+1}/{len(review_divs)}: {review_id}")
                    
                    # Check if there's an expand button
                    expand_btn = review_div.find_elements(By.CSS_SELECTOR, f"a.unfold#toggle-{review_id}-copy")
                    
                    if expand_btn:
                        # Scroll the expand button into view
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", expand_btn[0])
                        time.sleep(1)
                        
                        # Try to click using JavaScript if regular click fails
                        try:
                            expand_btn[0].click()
                        except:
                            driver.execute_script("arguments[0].click();", expand_btn[0])
                        
                        # Wait longer for content to expand
                        time.sleep(2)
                        
                        # Wait for the expanded content to appear
                        try:
                            # Try multiple possible selectors for expanded content
                            content_selectors = [
                                "div.review-content.clearfix",
                                "div.review-content", 
                                f"div#toggle-{review_id}-copy-content",
                                "div.full-content"
                            ]
                            
                            content_div = None
                            for selector in content_selectors:
                                elements = review_div.find_elements(By.CSS_SELECTOR, selector)
                                if elements:
                                    content_div = elements[0]
                                    break
                            
                            if not content_div:
                                print(f"⚠️ Could not find expanded content for review {review_id}")
                                continue

                        except Exception as e:
                            print(f"⚠️ Error waiting for expanded content: {e}")
                            continue
                    else:
                        # No expand button, get content directly
                        content_div = review_div.find_element(By.CSS_SELECTOR, "div.review-content.clearfix")

                    # Extract text from paragraphs
                    ps = content_div.find_elements(By.TAG_NAME, "p")
                    full_text = "\n".join([p.text.strip() for p in ps if p.text.strip()])
                    
                    # If no paragraphs, try getting all text from the content div
                    if not full_text.strip():
                        full_text = content_div.text.strip()
                    
                    # Skip if still empty
                    if not full_text.strip():
                        print(f"⚠️ Empty review text for {review_id}, skipping.")
                        continue

                    # Get URL - try different attributes
                    url_attr = None
                    for attr in ['data-url', 'href']:
                        url_attr = content_div.get_attribute(attr)
                        if url_attr:
                            break
                    
                    # If no URL in content div, construct it
                    if not url_attr:
                        url_attr = f"https://movie.douban.com/review/{review_id}/"

                    # Build review dict
                    review_data = {
                        "title": title,
                        "review_text": full_text,
                        "stars": rating,
                        "url": url_attr,
                    }
                    all_reviews.append(review_data)
                    print(f"✅ Successfully scraped review {review_id} ({len(full_text)} chars)")

                except Exception as e:
                    print(f"⚠️ Error processing review: {str(e)}")
                    continue

            # Move to next page
            start += 20
            time.sleep(2)  # Be nice to the server

    # Save to CSV
    if all_reviews:
        df = pd.DataFrame(all_reviews)
        output_path = os.path.join(output_folder, f"{title}.csv")
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"✅ Saved {len(df)} reviews for '{title}' to {output_path}")
    else:
        print(f"⚠️ No reviews found for '{title}'")

# === RUN SCRIPT ===
for title, movie_id in titles.items():
    scrape_movie_reviews(title, movie_id)