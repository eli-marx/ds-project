import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import random
import csv

def makeRandomAgent():
    ua = UserAgent()
    try:
        user_agent = ua.random
    except:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...'  # fallback UA

    return user_agent


def scrape_reviews():
    url = "https://movie.douban.com/subject/30314848/comments?percent_type=l&start=0&limit=20&status=P&sort=new_score"
    all_reviews = []

    headers = {
        "User-Agent": makeRandomAgent()
    }

    response = requests.get(url, headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Used User-Agent: {headers['User-Agent']}")

    soup = BeautifulSoup(response.text, 'html.parser')

    review_divs = soup.find_all('div', class_='comment-item')
    
    for review in review_divs:

        if review:
            # Extract the comment text
            comment_text = review.find('p', class_='comment-content')
            
            if comment_text:
                print(f"Comment: {comment_text.get_text().strip()}")
            else:
                print("Could not find comment text")
        else:
            print("\n--- No comments found ---")
            print("Let's investigate what's on the page...")
            
            # Print first 1000 characters to see what we got
            print("\nFirst 1000 characters of the page:")
            print(response.text[:1000])
            
            # Look for any div elements to see the page structure
            print("\nAll div elements on the page:")
            divs = soup.find_all('div')
            for i, div in enumerate(divs[:5]):  # Show first 5 divs
                print(f"Div {i+1} classes: {div.get('class')}")
                print(f"Div {i+1} text (first 50 chars): {div.get_text()[:50]}...")
                print("---")

def main():
    scrape_reviews()

if __name__ == "__main__":
    main()