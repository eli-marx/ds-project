import requests
from bs4 import BeautifulSoup
import time
import random
import csv
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

def save_to_csv(reviews, filename=None):
    """Save reviews to CSV file"""
    if not reviews:
        print("No reviews to save")
        return
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"douban_reviews_{timestamp}.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['name', 'rating', 'time', 'comment', 'title']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write reviews
            for review in reviews:
                writer.writerow(review)
        
        print(f"\nSaved {len(reviews)} reviews to {filename}")
        
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def scrape_all_pages(base_url, title, limit_per_page=20, max_pages=50):
    """
    Scrape all pages until no more reviews are found
    :param base_url: URL without start parameter
    :param limit_per_page: Number of reviews per page (usually 20)
    :param max_pages: Safety limit to prevent infinite loops
    """
    all_reviews = []
    current_page = 0

    while current_page < max_pages:
        print(f"\n{'='*50}")
        print(f"Scraping page {current_page + 1} (starting from review #{current_page * limit_per_page})")
        print(f"{'='*50}")
        
        # Construct URL for current page
        base_without_start = base_url.split('&start=')[0] if '&start=' in base_url else base_url
        url = f"{base_without_start}&start={current_page * limit_per_page}"
        print(f"URL: {url}")
        
        # Scrape the page
        page_reviews = scrape_single_page(url, title)
        
        # Check if we got any reviews
        if not page_reviews:
            print(f"No reviews found on page {current_page + 1}. We've reached the end!")
            break
        
        # Check if we got fewer reviews than expected (last page)
        all_reviews.extend(page_reviews)
        print(f"Successfully scraped {len(page_reviews)} reviews from page {current_page + 1}")
        print(f"Total reviews collected so far: {len(all_reviews)}")
        
        # If we got fewer than the limit, this is the last page
        if len(page_reviews) < limit_per_page:
            print(f"Got {len(page_reviews)} reviews (less than {limit_per_page}). This appears to be the last page!")
            break
        
        # Prepare for next page
        current_page += 1
        
        # Random delay between pages (but not after the last page)
        delay = random.uniform(5, 10)
        print(f"Waiting {delay:.1f} seconds before next page...")
        time.sleep(delay)
    
    if current_page >= max_pages:
        print(f"\nWarning: Reached maximum page limit ({max_pages}). There might be more reviews available.")
    
    return all_reviews

def scrape_multiple_pages(base_url, num_pages=5):
    """Scrape a specific number of pages (keeping old function for backward compatibility)"""
    all_reviews = []
    
    # The base URL should NOT include the start parameter
    # We'll build it properly for each page
    
    for page in range(num_pages):
        print(f"\n{'='*50}")
        print(f"Scraping page {page + 1}/{num_pages}")
        print(f"{'='*50}")
        
        # Construct URL with proper pagination
        # Remove any existing start parameter from the base URL first
        base_without_start = base_url.split('&start=')[0] if '&start=' in base_url else base_url
        url = f"{base_without_start}&start={page * 20}"
        print(f"URL: {url}")
        
        # Use the base scraping function with modified URL
        page_reviews = scrape_single_page(url)
        
        if page_reviews:
            all_reviews.extend(page_reviews)
            print(f"Successfully scraped {len(page_reviews)} reviews from page {page + 1}")
        else:
            print(f"No reviews found on page {page + 1}")
        
        # Random delay between pages to avoid rate limiting
        if page < num_pages - 1:  # Don't wait after the last page
            delay = random.uniform(5, 10)
            print(f"Waiting {delay:.1f} seconds before next page...")
            time.sleep(delay)
    
    return all_reviews

def scrape_single_page(url, title):
    """Modified version of scrape_reviews to work with any URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=10)
        print(f"Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Got non-200 status code: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for anti-bot indicators
        if any(indicator in response.text for indicator in ["请输入验证码", "验证码", "访问过于频繁", "请求过于频繁"]):
            print("Detected anti-bot measure!")
            return []
        
        comment_items = soup.find_all('div', class_='comment-item')
        print(f"Found {len(comment_items)} comment items")
        
        reviews = []
        
        for i, item in enumerate(comment_items):
            review_data = {
                'name': '',
                'comment': '',
                'rating': '',
                'time': '',
                'title': title
            }
            
            try:
                # Extract name - it's in comment-info span, in a link to douban.com/people/
                name_elem = None
                
                # Method 1: Look for name in comment-info section
                comment_info = item.find('span', class_='comment-info')
                if comment_info:
                    name_elem = comment_info.find('a', href=lambda x: x and 'douban.com/people/' in x)
                
                # Method 2: Look anywhere for link to people profile
                if not name_elem:
                    name_elem = item.find('a', href=lambda x: x and 'douban.com/people/' in x)
                
                # Method 3: Look for link with class 'u' (sometimes used)
                if not name_elem:
                    name_elem = item.find('a', class_='u')
                
                if name_elem:
                    review_data['name'] = name_elem.get_text().strip()
                
                # Extract comment text
                comment_elem = item.find('p', class_='comment-content')
                if comment_elem:
                    comment_text = comment_elem.get_text().strip()
                    review_data['comment'] = comment_text
                
                # Extract rating
                rating_elem = item.find('span', class_=lambda x: x and 'allstar' in str(x))
                if rating_elem:
                    rating_class = rating_elem.get('class', [])
                    for cls in rating_class:
                        if 'allstar' in cls and cls != 'allstar':
                            rating_num = ''.join(filter(str.isdigit, cls))
                            if rating_num:
                                stars = int(rating_num) // 10
                                review_data['rating'] = f"{stars}"
                
                # Extract time
                time_elem = item.find('span', class_='comment-time')
                if time_elem:
                    time_text = time_elem.get_text().strip()
                    review_data['time'] = time_text
                
                if review_data['comment']:
                    reviews.append(review_data)
                
            except Exception as e:
                print(f"Error processing comment {i+1}: {e}")
                continue
        
        return reviews
        
    except Exception as e:
        print(f"Error scraping page: {e}")
        return []

def main():
    print("Starting Douban movie comments scraper...")
    
    titles = {'Avatar': '1652587', 
          'Avatar: The Way of Water': '4811774', 
          'Jurassic World: Fallen Kingdom': '26416062', 
          'Transformers: The Last Knight': '25824686', 
          'Zootopia': '25662329', 
          'Warcraft': '2131940', 
          'Avengers: Age of Ultron': '10741834', 
          'Fast & Furious Presents: Hobbs & Shaw': '27163278', 
          'Jurassic World': '10440138', 
          'Spider-Man: Far From Home': '26931786', 
          'Ready Player One': '4920389'}

    for title in titles:
        print("\nOption 3: Scraping ALL pages...")
        base_url = f"https://movie.douban.com/subject/{titles[title]}/comments?percent_type=l&limit=20&status=P&sort=new_score"
        all_reviews = scrape_all_pages(base_url, title, limit_per_page=20, max_pages=100)
        
        if all_reviews:
            save_to_csv(all_reviews, f'{title}_douban_reviews_all_pages.csv')
            print(f"\nTotal reviews collected: {len(all_reviews)}")
        
if __name__ == "__main__":
    main()