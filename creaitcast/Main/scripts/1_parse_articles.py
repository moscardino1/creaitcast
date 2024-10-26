from dotenv import load_dotenv
import os
load_dotenv()
# Hugging Face API endpoint and token
API_KEY = os.getenv('newsapi')
import sys
import os
import logging
from newsapi import NewsApiClient
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# You'll need to sign up for a free API key at https://newsapi.org/


def fetch_articles(num_articles):
    newsapi = NewsApiClient(api_key=API_KEY)
    
    # Calculate date range for yesterday
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    query='bitcoin'
    logger.info(f"Fetching {query}-related articles from NewsAPI for {yesterday}")
    
    try:
        response = newsapi.get_everything(
                                          q=query,
                                          language='en',
                                          sort_by='relevancy',#'popularity',#'publishedAt',#'relevancy',
                                          from_param=yesterday,#2024-09-24',#yesterday,
                                          to=today,
                                          page_size=num_articles)
        
        if response['status'] == 'ok':
            return [(article['title'], article['url'], article['source']['name']) for article in response['articles']]
        else:
            logger.error(f"API returned an error: {response.get('message', 'Unknown error')}")
            return []
    
    except Exception as e:
        logger.error(f"Error fetching articles: {str(e)}")
        return []

def fetch_full_article(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find the main content
        content = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
        if content:
            # Remove unwanted elements
            for element in content(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            # Extract text, preserving paragraph structure
            paragraphs = content.find_all('p')
            text = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            return text
        else:
            logger.warning(f"Content not found for {url}")
            return None
    except Exception as e:
        logger.error(f"Error fetching full article content from {url}: {str(e)}")
        return None

def main(podcast_number, num_articles):
    output_folder = f"output/podcast_{podcast_number}/articles"
    os.makedirs(output_folder, exist_ok=True)
    
    articles = fetch_articles(num_articles)

    for i, (title, url, source) in enumerate(articles, 1):
        try:
            content = fetch_full_article(url)
            if content:
                with open(os.path.join(output_folder, f"article_{i}.txt"), "w", encoding="utf-8") as f:
                    f.write(f"Title: {title}\n\n")
                    f.write(f"Source: {source}\n\n")
                    f.write(f"URL: {url}\n\n")
                    f.write(f"Content:\n{content}")
                logger.info(f"Successfully processed article {i} from {source}")
            else:
                logger.warning(f"Skipping article {i} from {source} due to content fetch failure")
        except Exception as e:
            logger.error(f"Error processing article {i} from {source}: {str(e)}")

    print(f"Processed {len(articles)} articles for podcast {podcast_number}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 1_parse_articles.py <podcast_number> <num_articles>")
        sys.exit(1)
    
    podcast_number = int(sys.argv[1])
    num_articles = int(sys.argv[2])
    main(podcast_number, num_articles)