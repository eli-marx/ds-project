import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === SETUP ===
# Replace with one movie from your `titles` dict
titles = {"Avatar": "1652587"}  # Replace this as needed
output_folder = "output1"
os.makedirs(output_folder, exist_ok=True)

# Set up Chrome driver
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)  # Keep browser open after script ends
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

# Prompt user to log in
driver.get("https://www.douban.com/")
input("Please log into Douban manually in the browser window. Press Enter here when done...")

# === FUNCTION TO SCRAPE ONE MOVIE ===
def scrape_movie_reviews(title, movie_id):
    all_reviews = []

    for rating in [1, 2]:  # 1-star and 2-star reviews
        start = 0
        while True:
            url = f"https://movie.douban.com/subject/{movie_id}/reviews?sort=hotest&rating={rating}&start={start}"
            driver.get(url)
            time.sleep(2)

            review_divs = driver.find_elements(By.CSS_SELECTOR, "div.main.review-item")
            if not review_divs:
                break  # No more reviews on this page

            for review_div in review_divs:
                try:
                    review_id = review_div.get_attribute("id")
                    expand_btn = review_div.find_elements(By.CSS_SELECTOR, f"a.unfold#toggle-{review_id}-copy")
                    if not expand_btn:
                        continue  # Skip short reviews

                    # Click "展开"
                    driver.execute_script("arguments[0].click();", expand_btn[0])
                    time.sleep(0.5)  # Allow time for DOM to update

                    try:
                        # Wait until the review content with <p> elements loads
                        content_div = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, f"div.review-content.clearfix"))
                        )

                        # Wait for at least one <p> inside the review content
                        WebDriverWait(driver, 5).until(
                            lambda d: len(content_div.find_elements(By.TAG_NAME, "p")) > 0
                        )

                        # Extract all non-empty paragraphs
                        ps = content_div.find_elements(By.TAG_NAME, "p")
                        full_text = "\n".join([p.text.strip() for p in ps if p.text.strip()])
                    except:
                        print(f"⚠️ Timeout or no <p> tags found for review {review_id}")
                        continue

                    # Skip if review text is still empty
                    if not full_text.strip():
                        print(f"⚠️ Empty review for {review_id}, skipping.")
                        continue

                    # Build review dict
                    review_data = {
                        "title": title,
                        "review_text": full_text,
                        "stars": rating,
                        "url": content_div.get_attribute("data-url"),
                    }
                    all_reviews.append(review_data)

                except Exception as e:
                    print(f"⚠️ Error processing review: {e}")
                    continue

            start += 20
            time.sleep(1)

    # Save to CSV
    df = pd.DataFrame(all_reviews)
    output_path = os.path.join(output_folder, f"{title}.csv")
    df.to_csv(output_path, index=False)
    print(f"✅ Saved {len(df)} reviews for '{title}' to {output_path}")


# === RUN SCRIPT FOR ONE MOVIE ===
for title, movie_id in titles.items():
    scrape_movie_reviews(title, movie_id)
    break  # Only do one movie for now