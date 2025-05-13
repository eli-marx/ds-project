import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Target URL (short comments for Everything Everywhere All At Once)
url = "https://movie.douban.com/subject/30314848/comments?limit=20&status=P&sort=new_score"

# Use a random user-agent to avoid getting blocked
headers = {
    "User-Agent": UserAgent().random
}

# Make the request
response = requests.get(url, headers=headers)

# Check the status
if response.status_code != 200:
    print("Failed to fetch page:", response.status_code)
else:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Select the first comment block
    comment_block = soup.select_one('.comment')
    
    if comment_block:
        username = comment_block.select_one('.comment-info a').text.strip()
        rating_tag = comment_block.select_one('.comment-info span.rating')
        rating = rating_tag['title'] if rating_tag else "No rating"
        comment_text = comment_block.select_one('.short').text.strip()
        date = comment_block.select_one('.comment-time')['title']

        print("Username:", username)
        print("Rating:", rating)
        print("Date:", date)
        print("Comment:", comment_text)
    else:
        print("No comments found.")