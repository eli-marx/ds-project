from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import os
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

def save_movie_csv(reviews, movie_title, output_folder="imdb_output"):
    """Save reviews for a specific movie to individual CSV file in output folder"""
    if not reviews:
        print(f"❌ No reviews to save for {movie_title}")
        return None
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"📁 Created output folder: {output_folder}")
    
    # Create safe filename
    safe_title = movie_title.replace(" ", "_").replace(":", "").replace("/", "_").replace("'", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_title}_reviews_{timestamp}.csv"
    filepath = os.path.join(output_folder, filename)
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['title', 'comment', 'rating']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for review in reviews:
                writer.writerow(review)
        
        print(f"💾 Saved {len(reviews)} reviews for '{movie_title}' to {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ Error saving movie CSV for {movie_title}: {e}")
        return None

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

    # Look for and click the "25 more" button to load additional reviews
    try:
        more_button = driver.find_element(By.XPATH, "//span[@class='ipc-see-more__text' and text()='25 more']")
        if more_button:
            print("🔍 Found '25 more' button, clicking to load additional reviews...")
            driver.execute_script("arguments[0].click();", more_button)
            
            # Wait a moment for the new reviews to load
            time.sleep(3)
            
            # Wait for additional reviews to be present
            try:
                WebDriverWait(driver, 10).until(
                    lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "article.user-review-item")) > 25
                )
                print("✅ Additional reviews loaded successfully.")
            except:
                print("⚠️ Additional reviews may not have loaded, continuing anyway...")
        else:
            print("ℹ️  No '25 more' button found, proceeding with available reviews.")
    except Exception as e:
        print(f"ℹ️  No '25 more' button found or error clicking it: {e}")
        print("📋 Proceeding with currently loaded reviews...")

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
    'The Shawshank Redemption': 'tt0111161',
    'Titanic': 'tt0120338',
    'Forrest Gump': 'tt0109830',
    'Spirited Away': 'tt0245429',
    'Life Is Beautiful': 'tt0118799',
    'Léon: The Professional': 'tt0110413',
    'Interstellar': 'tt0816692',
    'Inception': 'tt1375666',
    'The Truman Show': 'tt0120382',
    "Schindler's List": 'tt0108052',
    'WALL·E': 'tt0910970',
    'The Intouchables': 'tt1675434',
    'The Godfather': 'tt0068646',
    'Coco': 'tt2380307',
    "Harry Potter and the Sorcerer's Stone": 'tt0241527',
    'The Dark Knight': 'tt0468569',
    'The Lord of the Rings: The Return of the King': 'tt0167260',
    'Up': 'tt1049413',
    '12 Angry Men': 'tt0050083',
    'Catch Me If You Can': 'tt0264464',
    'Life of Pi': 'tt0454876',
    'The Pianist': 'tt0253474',
    'Green Book': 'tt6966692',
    'The Matrix': 'tt0133093',
    'The Lion King': 'tt0110357',
    'Fight Club': 'tt0137523',
    'The Curious Case of Benjamin Button': 'tt0421715',
    'A Beautiful Mind': 'tt0268978',
    'Lock, Stock and Two Smoking Barrels': 'tt0120735',
    'Avatar': 'tt0499549',
    'Saving Private Ryan': 'tt0120815',
    'The Silence of the Lambs': 'tt0102926',
    "One Flew Over the Cuckoo's Nest": 'tt0073486',
    'The Grand Budapest Hotel': 'tt2278388',
    'Shutter Island': 'tt1130884',
    'The Prestige': 'tt0482571',
    'Good Will Hunting': 'tt0119217',
    'Pulp Fiction': 'tt0110912',
    'Pirates of the Caribbean: The Curse of the Black Pearl': 'tt0325980',
    'Se7en': 'tt0114369',
    'Parasite': 'tt6751668',
    'The Sixth Sense': 'tt0167404',
    'Inside Out': 'tt2096673',
    'Gone Girl': 'tt2267998',
    'How to Train Your Dragon': 'tt0892769',
    'Monsters, Inc.': 'tt0198781',
    'Toy Story 3': 'tt0435761',
    'Django Unchained': 'tt1853728',
    'The Imitation Game': 'tt2084970',
    'Psycho': 'tt0054215',
    'Hacksaw Ridge': 'tt2119532',
    'Joker': 'tt7286456',
    'The Bourne Ultimatum': 'tt0440963',
    'The Green Mile': 'tt0120689',
    '2001: A Space Odyssey': 'tt0062622',
    'Memento': 'tt0209144',
    'Slumdog Millionaire': 'tt1010048',
    'Mad Max: Fury Road': 'tt1392190',
    'Whiplash': 'tt2582802',
    'Bohemian Rhapsody': 'tt1727824',
    'Black Swan': 'tt0947798',
    'La La Land': 'tt3783958',
    'Terminator 2: Judgment Day': 'tt0103064',
    'Inglourious Basterds': 'tt0361748',
    'The Notebook': 'tt0332280',
    'The Martian': 'tt3659388',
    'Spider-Man: Into the Spider-Verse': 'tt4633694',
    'Frozen': 'tt2294629'
    }

    dif = ['Whiplash',
 'Bohemian Rhapsody',
 'Black Swan',
 'La La Land',
 'Terminator 2: Judgment Day',
 'Inglourious Basterds',
 'The Notebook',
 'The Martian',
 'Spider-Man: Into the Spider-Verse',
 'Frozen']

    titles = {key: titles[key] for key in dif if key in titles}


    # Main scraping loop
    all_reviews = []
    total_reviews_count = 0
    processed_movies = []

    for MANUAL_TITLE in titles.keys():
        ID = titles[MANUAL_TITLE]
        print(f"\n🚀 Starting scrape for {MANUAL_TITLE}, id: {ID}")
        print(f"📊 Will scrape ratings 1 through 4...")
        
        movie_reviews = []  # Store reviews for this specific movie
        
        try:
            for rating in range(1, 5):  # This will loop through 1, 2, 3, 4
                MANUAL_RATING = str(rating)

                # Scrape reviews for this rating
                review_data = scrape_reviews_for_rating(driver, rating, ID, MANUAL_TITLE)
                
                # Add reviews to both master list and movie-specific list
                if review_data:
                    all_reviews.extend(review_data)
                    movie_reviews.extend(review_data)
                    total_reviews_count += len(review_data)
                    print(f"📋 Processed {len(review_data)} reviews for {rating}-star rating")
                else:
                    print(f"❌ No reviews found for {rating}-star rating")
                
                # Add a small delay between requests to be respectful
                if rating < 4:  # Don't wait after the last iteration
                    print(f"⏳ Waiting 3 seconds before next rating...")
                    time.sleep(3)
            
            # Save individual movie CSV after completing all ratings for this movie
            if movie_reviews:
                saved_path = save_movie_csv(movie_reviews, MANUAL_TITLE)
                if saved_path:
                    processed_movies.append({
                        'title': MANUAL_TITLE,
                        'reviews_count': len(movie_reviews),
                        'file_path': saved_path
                    })
                    print(f"✅ Completed {MANUAL_TITLE}: {len(movie_reviews)} total reviews")
                else:
                    print(f"⚠️ Failed to save CSV for {MANUAL_TITLE}")
            else:
                print(f"❌ No reviews found for {MANUAL_TITLE}")
                
        except Exception as e:
            print(f"❌ Error processing {MANUAL_TITLE}: {e}")
            # Save what we have for this movie even if there was an error
            if movie_reviews:
                save_movie_csv(movie_reviews, MANUAL_TITLE)
        
        print(f"🏁 Finished processing {MANUAL_TITLE}")
        print(f"⏳ Waiting 5 seconds before next movie...")
        time.sleep(5)

    # Summary
    print(f"\n{'🎉 SCRAPING COMPLETE 🎉':^60}")
    print(f"📊 Total reviews scraped: {total_reviews_count}")
    print(f"🎬 Movies processed: {len(processed_movies)}")
    print(f"📁 Individual CSV files saved in 'imdb_output' folder")
    print(f"📁 Ratings scraped: 1, 2, 3, 4 stars")

    # Print summary of processed movies
    if processed_movies:
        print(f"\n📋 PROCESSED MOVIES SUMMARY:")
        print(f"{'Movie Title':<50} {'Reviews':<10} {'Status'}")
        print("="*70)
        for movie in processed_movies:
            print(f"{movie['title']:<50} {movie['reviews_count']:<10} {'✅ Saved'}")

    # Save all reviews to one combined file (keep original functionality)
    if all_reviews:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_filename = f"ALL_MOVIES_REVIEWS_{timestamp}.csv"
        
        try:
            with open(combined_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['title', 'comment', 'rating']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for review in all_reviews:
                    writer.writerow(review)
            print(f"✅ All reviews also saved to combined file: {combined_filename}")
        except Exception as e:
            print(f"❌ Error saving combined file: {e}")
    else:
        print("❌ No reviews to save.")

    # Close the browser
    driver.quit()

if __name__ == "__main__":
    main()