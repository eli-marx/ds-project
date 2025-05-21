from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
from datetime import datetime

def save_to_csv(reviews, filename=None):
    """Save reviews to CSV file"""
    if not reviews:
        print("No reviews to save")
        return

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = MANUAL_TITLE.replace(" ", "_").replace(":", "").replace("/", "_")
        filename = f"{safe_title}_rating_{MANUAL_RATING}_reviews_.csv"

    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['title', 'comment', 'rating']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for review in reviews:
                writer.writerow(review)

        print(f"\n✅ Saved {len(reviews)} reviews to {filename}")
    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")

def scrape_reviews_for_rating(driver, rating, MOVIE_ID, MANUAL_TITLE):
    """Scrape reviews for a specific rating"""
    url = f"https://www.imdb.com/title/{MOVIE_ID}/reviews/?ref_=tt_ururv_sm&sort=featured%2Casc&rating={rating}"
    
    print(f"\n{'='*60}")
    print(f"🎬 Scraping reviews for: {MANUAL_TITLE}")
    print(f"⭐ Rating: {rating} stars")
    print(f"🔗 URL: {url}")
    print(f"{'='*60}")
    
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article.user-review-item"))
        )
        print("✅ Reviews loaded.")
    except:
        print("❌ Timed out loading reviews.")
        driver.save_screenshot(f"debug_timeout_rating_{rating}.png")
        return []

    # Expand all spoiler buttons first
    spoiler_buttons = driver.find_elements(By.CLASS_NAME, "review-spoiler-button")
    for btn in spoiler_buttons:
        try:
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Could not click spoiler button: {e}")
            continue

    # Get all review articles
    reviews = driver.find_elements(By.CSS_SELECTOR, "article.user-review-item")
    print(f"🧾 Found {len(reviews)} reviews.\n")

    # List to store all review data for this rating
    review_data = []

    for review in reviews:
        try:
            # Optional: Get review title if available (this is the review's own title, not the movie title)
            try:
                review_title_elem = review.find_element(By.CSS_SELECTOR, '[data-testid="review-summary"] h3')
                review_title = review_title_elem.text.strip()
            except:
                review_title = "[No review title]"

            # Get the full text content from the visible div
            content_elem = review.find_element(By.CSS_SELECTOR, 'div.ipc-html-content-inner-div[role="presentation"]')
            content = content_elem.text.strip()

            # Create review dictionary for CSV
            review_dict = {
                'title': MANUAL_TITLE,
                'comment': content,
                'rating': str(rating)
            }
            
            # Add to our data list
            review_data.append(review_dict)

            # # Print to screen (as before)
            # print(f"Movie Title: {MANUAL_TITLE}")
            # print(f"Review Title: {review_title}")
            # print(f"Rating: {rating}")
            # print(f"Content: {content}\n{'-'*50}")
            
        except Exception as e:
            print(f"⚠️ Skipping a review due to error: {e}")
            continue

    return review_data

def main():
    """Main function to orchestrate the scraping process"""
    # Initialize visible Chrome for debugging
    options = webdriver.ChromeOptions()
    # Comment this out to watch the browser
    # options.add_argument("--headless")  
    driver = webdriver.Chrome(options=options)

    # MANUAL SETTINGS - Change these values as needed
    titles = {
    'Aquaman': 'tt1477834',
    'Avatar': 'tt0499549',
    'Avatar: The Way of Water': 'tt1630029',
    'Avengers: Age of Ultron': 'tt2395427',
    'Avengers: Endgame': 'tt4154796',
    'Avengers: Infinity War': 'tt4154756',
    'Everything Everywhere All at Once': 'tt6710474',
    'Fast & Furious Presents: Hobbs & Shaw': 'tt6806448',
    'Furious 7': 'tt2820852',
    'Jurassic World': 'tt0369610',
    'Jurassic World: Fallen Kingdom': 'tt4881806',
    'Ready Player One': 'tt1677720',
    'Spider-Man: Far From Home': 'tt6320628',
    'The Fate of the Furious': 'tt4630562',
    'Transformers: Age of Extinction': 'tt2109248',
    'Transformers: The Last Knight': 'tt3371366',
    'Venom': 'tt1270797',
    'Warcraft': 'tt0803096',
    'Zootopia': 'tt2948356'
    }

    # Main scraping loop - iterate through ratings 1 to 4
    all_reviews = []
    total_reviews_count = 0

    for MANUAL_TITLE in titles.keys():
        ID = titles[MANUAL_TITLE]
        print(f"🚀 Starting scrape for {MANUAL_TITLE}, id: {ID}")
        print(f"📊 Will scrape ratings 1 through 4...")
        try:
            for rating in range(1, 5):  # This will loop through 1, 2, 3, 4
                MANUAL_RATING = str(rating)

                # Scrape reviews for this rating
                review_data = scrape_reviews_for_rating(driver, rating, ID, MANUAL_TITLE)
                
                # Add reviews to the master list
                if review_data:
                    all_reviews.extend(review_data)
                    total_reviews_count += len(review_data)
                    print(f"📋 Processed {len(review_data)} reviews for {rating}-star rating")
                else:
                    print(f"❌ No reviews found for {rating}-star rating")
                
                # Add a small delay between requests to be respectful
                if rating < 4:  # Don't wait after the last iteration
                    print(f"⏳ Waiting 3 seconds before next rating...")
                    time.sleep(3)
        finally:
            print("finished a thing")
        

    # Summary
    print(f"\n{'🎉 SCRAPING COMPLETE 🎉':^60}")
    print(f"📊 Total reviews scraped: {total_reviews_count}")
    print(f"📁 Ratings scraped: 1, 2, 3, 4 stars")
    print(f"💾 All reviews will be saved to one combined CSV file")

    # Save all reviews to one combined file
    if all_reviews:
        safe_title = MANUAL_TITLE.replace(" ", "_").replace(":", "").replace("/", "_")
        combined_filename = f"{safe_title}_ALL_RATINGS_reviews_.csv"
        
        try:
            with open(combined_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['title', 'comment', 'rating']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for review in all_reviews:
                    writer.writerow(review)
            print(f"✅ All reviews saved to {combined_filename}")
        except Exception as e:
            print(f"❌ Error saving combined file: {e}")
    else:
        print("❌ No reviews to save.")

     
    # Close the browser
    driver.quit()

if __name__ == "__main__":
    main()