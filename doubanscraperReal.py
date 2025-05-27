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

  'The Shawshank Redemption': '1292052',
  'Titanic': '1292722',
  'Forrest Gump': '1292720',
  'Spirited Away': '1291561',
  'Life Is Beautiful': '1292063',
  'Léon: The Professional': '1295644',
  'Interstellar': '1889243',
  'Inception': '3541415',
  'The Truman Show': '1292064',
  "Schindler's List": '1295124',
  'WALL·E': '2131459',
  'The Intouchables': '6786002',
  'The Godfather': '1291841',
  'Coco': '20495023',
  "Harry Potter and the Sorcerer's Stone": '1295038',
  'The Dark Knight': '1851857',
  'The Lord of the Rings: The Return of the King': '1291552',
  'Up': '2129039',
  '12 Angry Men': '1293182',
  'Catch Me If You Can': '1305487',
  'Life of Pi': '1929463',
  'The Pianist': '1296736',
  'Green Book': '27060077',
  'The Matrix': '1291843',
  'The Lion King': '1301753',
  'Fight Club': '1292000',
  'The Curious Case of Benjamin Button': '1485260',
  'A Beautiful Mind': '1306029',
  'Lock, Stock and Two Smoking Barrels': '1293350',
  'Avatar': '1652587',
  'Saving Private Ryan': '1292849',
  'The Silence of the Lambs': '1293544',
  "One Flew Over the Cuckoo's Nest": '1292224',
  'The Grand Budapest Hotel': '11525673',
  'Shutter Island': '2334904',
  'The Prestige': '1780330',
  'Good Will Hunting': '1292656',
  'Pulp Fiction': '1291832',
  'Pirates of the Caribbean: The Curse of the Black Pearl': '1298070',
  'Se7en': '1292223',
  'Parasite': '27010768',
  'The Sixth Sense': '1297630',
  'Inside Out': '10533913',
  'Gone Girl': '21318488',
  'How to Train Your Dragon': '2353023',
  'Monsters, Inc.': '1291579',
  'Toy Story 3': '1858711',
  'Django Unchained': '6307447',
  'The Imitation Game': '10463953',
  'Psycho': '1293181',
  'Hacksaw Ridge': '26325320',
  'Joker': '27119724',
  'The Bourne Ultimatum': '1578507',
  'The Green Mile': '1300374',
  '2001: A Space Odyssey': '1292226',
  'Memento': '1304447',
  'Slumdog Millionaire': '2209573',
  'Mad Max: Fury Road': '3592854',
  'Whiplash': '25773932',
  'Bohemian Rhapsody': '5300054',
  'Black Swan': '1978709',
  'La La Land': '25934014',
  'Terminator 2: Judgment Day': '1291844',
  'Inglourious Basterds': '1438652',
  'The Notebook': '1309163',
  'The Martian': '25864085',
  'Spider-Man: Into the Spider-Verse': '26374197',
  'Frozen': '4202982',
}
output_folder = "douban_outputREAL"
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