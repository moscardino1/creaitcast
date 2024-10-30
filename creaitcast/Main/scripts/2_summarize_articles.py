import os
import sys
import logging
import requests
import time
from time import sleep
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HF_API_KEY = os.getenv('HF')

# Initialize logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_memory_usage():
    """Get current memory usage of the process"""
    import psutil
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # Convert to MB

class HFAPISummarizer:
    def __init__(self, api_token):
        """Initialize with just the API token and URL"""
        self.API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        self.headers = {"Authorization": f"Bearer {api_token}"}
    
    def summarize(self, text, max_length=800, min_length=50):
        """Simplified summarization function that only makes API calls"""
        if not text or len(text.strip()) == 0:
            return ""
            
        # Truncate text if it's too long (BART's limit is around 1024 tokens)
        max_chars = 4000
        if len(text) > max_chars:
            logger.warning(f"Text truncated from {len(text)} to {max_chars} characters")
            text = text[:max_chars]

        payload = {
            "inputs": text,
            "parameters": {
                "max_length": max_length,
                "min_length": min_length,
                "do_sample": False
            }
        }

        # Implement retry logic with backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.API_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=30  # Add timeout
                )
                
                if response.status_code == 200:
                    return response.json()[0]['summary_text']
                    
                elif response.status_code == 503:
                    wait_time = 2 ** attempt
                    logger.warning(f"Model loading, waiting {wait_time} seconds...")
                    sleep(wait_time)
                    
                else:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    response.raise_for_status()
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    return text[:max_length]
                sleep(2 ** attempt)
                
        return text[:max_length]

def process_single_article(file_path, summarizer):
    """Process a single article with minimal memory footprint"""
    logger.info(f"Processing {file_path}")
    logger.info(f"Current memory usage: {get_memory_usage():.2f} MB")
    
    try:
        # Read file in chunks if needed
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract title and content
        title = content.split('\n')[0].replace("Title: ", "").strip()
        article_text = content.split('Content:\n')[1].strip()
        
        # Clear content variable
        content = None
        
        # Get summary
        summary = summarizer.summarize(article_text)
        
        # Create output path
        input_folder = os.path.dirname(file_path)
        output_folder = input_folder.replace("articles", "summaries")
        os.makedirs(output_folder, exist_ok=True)
        
        # Generate output filename
        index = os.path.basename(file_path).split('_')[1].split('.')[0]
        output_file = os.path.join(output_folder, f"summary_{index}.txt")
        
        # Write summary
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\nSummary:\n{summary}")
            
        logger.info(f"Successfully summarized article {index}")
        logger.info(f"Summary length: {len(summary)} characters")
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")

def main(podcast_number, num_articles):
    """Main function with minimal memory usage"""
    logger.info(f"Starting summarization for podcast {podcast_number}")
    logger.info(f"Initial memory usage: {get_memory_usage():.2f} MB")
    
    # Check API token
    if not HF_API_KEY:
        logger.error("Please set your HuggingFace API token as HF environment variable")
        sys.exit(1)
    
    # Initialize summarizer
    summarizer = HFAPISummarizer(HF_API_KEY)
    
    # Get input folder
    input_folder = f"output/podcast_{podcast_number}/articles"
    if not os.path.exists(input_folder):
        logger.error(f"Input folder not found: {input_folder}")
        sys.exit(1)
    
    # Get article files
    article_files = [
        f for f in os.listdir(input_folder)
        if f.startswith("article_") and f.endswith(".txt")
    ]
    article_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    
    # Limit to num_articles if specified
    if num_articles > 0:
        article_files = article_files[:num_articles]
    
    # Process articles one at a time
    for article_file in article_files:
        file_path = os.path.join(input_folder, article_file)
        process_single_article(file_path, summarizer)
        
        # Add a small delay between articles to prevent API rate limiting
        time.sleep(1)
        
        # Log memory usage
        logger.info(f"Memory usage after article: {get_memory_usage():.2f} MB")

    logger.info(f"Completed summarization for podcast {podcast_number}")
    logger.info(f"Final memory usage: {get_memory_usage():.2f} MB")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 2_summarize_articles.py <podcast_number> <num_articles>")
        sys.exit(1)
        
    podcast_number = int(sys.argv[1])
    num_articles = int(sys.argv[2])
    main(podcast_number, num_articles)