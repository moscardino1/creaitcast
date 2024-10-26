import os
import sys
import logging
from transformers import pipeline
from concurrent.futures import ProcessPoolExecutor

# Initialize logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load the multilingual summarization model
# Using mT5 model which supports Italian and many other languages
summarizer = pipeline("summarization", model="facebook/mbart-large-cc25", 
                     tokenizer="facebook/mbart-large-cc25")

def summarize_text(text, max_chunk_length=1000, max_summary_length=500):
    """Summarizes the provided Italian text into a single summary."""
    try:
        # Split text into chunks
        chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]
        if not chunks:
            return text  # Handle empty text case

        # Summarize chunks in batch with specific language settings
        chunk_summaries = summarizer(chunks, 
                                   max_length=max_summary_length // len(chunks), 
                                   min_length=30,
                                   do_sample=False,
                                   forced_bos_token_id=summarizer.tokenizer.lang_code_to_id["it_IT"])
        
        summaries = [summary['summary_text'] for summary in chunk_summaries]

        # Combine and summarize if necessary
        full_summary = " ".join(summaries)
        if len(full_summary) > max_summary_length:
            full_summary = summarizer(full_summary, 
                                    max_length=max_summary_length, 
                                    min_length=200,
                                    do_sample=False,
                                    forced_bos_token_id=summarizer.tokenizer.lang_code_to_id["it_IT"])[0]['summary_text']

        return full_summary
    except Exception as e:
        logger.error(f"Summarization failed: {str(e)}")
        return text  # Return original text as fallback

def process_article(article_file, index):
    """Processes a single Italian article file and returns its summary."""
    input_folder = os.path.dirname(article_file)
    output_folder = os.path.join(input_folder.replace("articles", "summaries"))

    os.makedirs(output_folder, exist_ok=True)
    
    try:
        with open(article_file, 'r', encoding='utf-8') as f:
            content = f.read()

        title = content.split('\n')[0].replace("Titolo: ", "").replace("Title: ", "")
        # Handle both Italian and English content markers
        if 'Contenuto:\n' in content:
            article_text = content.split('Contenuto:\n')[1]
        else:
            article_text = content.split('Content:\n')[1]

        summary = summarize_text(article_text)

        output_file = os.path.join(output_folder, f"summary_{index}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Titolo: {title}\nRiassunto:\n{summary}")

        logger.info(f"Riassunto articolo {index}")
    except Exception as e:
        logger.error(f"Errore nell'elaborazione dell'articolo {article_file}: {str(e)}")

def main(podcast_number, num_articles):
    input_folder = f"output/podcast_{podcast_number}/articles"
    
    available_articles = [f for f in os.listdir(input_folder) if f.startswith("article_") and f.endswith(".txt")]
    available_articles.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    
    # Use ProcessPoolExecutor for parallel processing
    with ProcessPoolExecutor() as executor:
        executor.map(process_article, 
                    [os.path.join(input_folder, article) for article in available_articles], 
                    range(1, len(available_articles) + 1))

    logger.info(f"Riassunti {len(available_articles)} articoli per il podcast {podcast_number}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Utilizzo: python 2_summarize_articles.py <numero_podcast> <numero_articoli>")
        sys.exit(1)

    podcast_number = int(sys.argv[1])
    num_articles = int(sys.argv[2])
    main(podcast_number, num_articles)