import os
import sys
import logging
import requests
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from dotenv import load_dotenv
import os
load_dotenv()



# Hugging Face API endpoint and token
HF_API_URL = "https://api-inference.huggingface.co/models/"
HF_API_KEY = os.getenv('HF')
# Initialize logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class HFAPISummarizer:
    def __init__(self, api_token):
        self.API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        self.headers = {"Authorization": f"Bearer {api_token}"}
        
    def summarize(self, text, max_length=500, min_length=30, retries=3):
        """Send request to HF API for summarization"""
        payload = {
            "inputs": text,
            "parameters": {
                "max_length": max_length,
                "min_length": min_length,
                "do_sample": False
            }
        }
        
        for attempt in range(retries):
            try:
                response = requests.post(self.API_URL, headers=self.headers, json=payload)
                if response.status_code == 200:
                    return response.json()[0]['summary_text']
                elif response.status_code == 503:
                    # Model is loading, wait and retry
                    sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    response.raise_for_status()
            except Exception as e:
                if attempt == retries - 1:
                    logger.error(f"Failed to get summary after {retries} attempts: {str(e)}")
                    return text
                sleep(2 ** attempt)
        return text

def summarize_text(text, summarizer, max_chunk_length=1000, max_summary_length=500):
    """Summarizes the provided text into a single summary using HF API."""
    try:
        # Split text into chunks if too long
        if len(text) > max_chunk_length:
            chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]
            summaries = []
            
            # Summarize each chunk
            for chunk in chunks:
                summary = summarizer.summarize(chunk, max_length=max_summary_length // len(chunks))
                summaries.append(summary)
            
            # Combine chunks and summarize again if needed
            full_summary = " ".join(summaries)
            if len(full_summary) > max_summary_length:
                full_summary = summarizer.summarize(full_summary, max_length=max_summary_length)
            
            return full_summary
        else:
            return summarizer.summarize(text, max_length=max_summary_length)
            
    except Exception as e:
        logger.error(f"Summarization failed: {str(e)}")
        return text

def process_article(args):
    """Processes a single article file and returns its summary."""
    article_file, index, summarizer = args
    input_folder = os.path.dirname(article_file)
    output_folder = os.path.join(input_folder.replace("articles", "summaries"))

    os.makedirs(output_folder, exist_ok=True)
    
    try:
        with open(article_file, 'r', encoding='utf-8') as f:
            content = f.read()

        title = content.split('\n')[0].replace("Title: ", "")
        article_text = content.split('Content:\n')[1]

        summary = summarize_text(article_text, summarizer)

        output_file = os.path.join(output_folder, f"summary_{index}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\nSummary:\n{summary}")

        logger.info(f"Summarized article {index}")
    except Exception as e:
        logger.error(f"Error processing article {article_file}: {str(e)}")

def main(podcast_number, num_articles, api_token):
    input_folder = f"output/podcast_{podcast_number}/articles"
    
    # Initialize summarizer with API token
    summarizer = HFAPISummarizer(api_token)
    
    available_articles = [f for f in os.listdir(input_folder) 
                         if f.startswith("article_") and f.endswith(".txt")]
    available_articles.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    
    # Use ThreadPoolExecutor instead of ProcessPoolExecutor since we're I/O bound with API calls
    with ThreadPoolExecutor(max_workers=3) as executor:
        args = [(os.path.join(input_folder, article), i+1, summarizer) 
                for i, article in enumerate(available_articles)]
        list(executor.map(process_article, args))

    logger.info(f"Summarized {len(available_articles)} articles for podcast {podcast_number}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 2_summarize_articles.py <podcast_number> <num_articles>")
        sys.exit(1)

    # Get your API token from HuggingFace
    api_token = HF_API_KEY
    if not api_token:
        print("Please set your HuggingFace API token as HF_API_TOKEN environment variable")
        sys.exit(1)

    podcast_number = int(sys.argv[1])
    num_articles = int(sys.argv[2])
    main(podcast_number, num_articles, api_token)