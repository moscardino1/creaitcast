import sys
import os
import logging
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fetch_zerohedge_articles():
    url = "https://www.zerohedge.com"
    logger.info(f"Fetching URL: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"Successfully fetched URL. Status code: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        logger.info("Successfully parsed HTML content")
        
        articles = soup.find_all('h2', class_='Article_title___TC6d')
        
        results = [(article.get_text(strip=True), article.find('a')['href']) for article in articles]
        return results
    
    except requests.RequestException as e:
        logger.error(f"Error fetching URL: {str(e)}")
        return []

def fetch_article_content(link):
    full_link = f"https://www.zerohedge.com{link}"
    logger.info(f"Fetching article content from: {full_link}")
    
    try:
        response = requests.get(full_link)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        content_div = soup.find('div', class_='NodeContent_body__HBEFs NodeBody_container__eeFKv')
        if content_div:
            return content_div.get_text(strip=True, separator=' ')
        else:
            logger.warning("Could not find the main content div.")
            return None
    except requests.RequestException as e:
        logger.error(f"Error fetching article: {str(e)}")
        return None

def process_article(title, link):
    content = fetch_article_content(link)
    return title, content if content else "Failed to fetch content."

def main(podcast_number, num_articles):
    output_folder = f"output/podcast_{podcast_number}/articles"
    
    articles = fetch_zerohedge_articles()
    articles = articles[:num_articles]

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_article, title, link) for title, link in articles]
        
        for i, future in enumerate(as_completed(futures), 1):
            try:
                title, content = future.result()
                with open(os.path.join(output_folder, f"article_{i}.txt"), "w", encoding="utf-8") as f:
                    f.write(f"Title: {title}\n\nContent:\n{content}")
            except Exception as e:
                logger.error(f"Error processing article: {str(e)}")

    print(f"Processed {num_articles} articles for podcast {podcast_number}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 1_parse_articles.py <podcast_number> <num_articles>")
        sys.exit(1)
    
    podcast_number = int(sys.argv[1])
    num_articles = int(sys.argv[2])
    main(podcast_number, num_articles)