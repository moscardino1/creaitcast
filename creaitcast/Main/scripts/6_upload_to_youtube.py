import os
import sys
import pickle
import requests
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import re
from collections import Counter

from dotenv import load_dotenv
import os
load_dotenv()



# Hugging Face API endpoint and token
HF_API_URL = "https://api-inference.huggingface.co/models/"
HF_API_KEY = os.getenv('HF')
# Initialize logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Replace this with your actual Hugging Face API key

def summarize_text(titles, model="facebook/bart-large-cnn", temperature=0.7):
    """Use Hugging Face API to summarize titles."""
    logger.debug(f"Attempting to summarize titles: {titles}")
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": " ".join(titles),
        "parameters": {
            "temperature": temperature,
            "max_length": 30  # Adjust max_length as needed
        }
    }
    logger.debug(f"API request data: {data}")

    try:
        response = requests.post(f"https://api-inference.huggingface.co/models/{model}", headers=headers, json=data)
        response.raise_for_status()
        summary = response.json()[0]['summary_text']
        logger.debug(f"API response: {response.json()}")
        return summary
    except requests.exceptions.RequestException as e:
        logger.error(f"Error summarizing titles: {str(e)}")
        logger.error(f"API response content: {response.content}")
        return None

def extract_keywords_from_summary(summary, num_keywords=5):
    """Extract keywords from the summarized text."""
    words = re.findall(r'\w+', summary.lower())
    word_freq = Counter(words)
    common_words = set(['the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'is', 'are', 'was', 'were', 'this', 'by'])
    keywords = [word for word, _ in word_freq.most_common(num_keywords * 2) if word not in common_words][:num_keywords]
    return keywords

def generate_ai_title_description(podcast_text, episode_number):
    try:
        logger.debug(f"Generating title and description for episode {episode_number}")
        logger.debug(f"Podcast text length: {len(podcast_text)}")

        # Split text to extract titles
        stories = re.findall(r"Our next story is titled: (.+?)(?=\n|\Z)", podcast_text)
        logger.debug(f"Extracted stories: {stories}")
        
        if not stories:
            logger.warning("No stories found in the podcast text")
            return f"Cronisphere Episode {episode_number}: AI-Generated News Summary", f"Welcome to Cronisphere Episode {episode_number}! In this episode, we bring you the latest AI-generated news summaries."

        # Summarize titles using AI
        summary = summarize_text(stories)
        logger.debug(f"Generated summary: {summary}")
        
        if not summary:
            logger.warning("Failed to generate summary")
            return f"Cronisphere Episode {episode_number}: AI-Generated News Summary", f"Welcome to Cronisphere Episode {episode_number}! In this episode, we bring you the latest AI-generated news summaries."

        # Extract keywords from the summarized titles
        keywords = extract_keywords_from_summary(summary, num_keywords=4)
        logger.debug(f"Extracted keywords: {keywords}")

        title = f"Cronisphere {episode_number}: {', '.join(keywords).title()}"

        # Create description
        description = f"Welcome to Cronisphere Episode {episode_number}!\n\n"
        description += "In this episode, we cover:\n\n"
        description += "\n".join(f"- {story}" for story in stories)
        description += "\n\nIn this episode, we bring you the latest AI-generated news summaries."

        logger.debug(f"Generated title: {title}")
        logger.debug(f"Generated description: {description[:100]}...")

        return title.strip(), description.strip()
    except Exception as e:
        logger.error(f"Error in generate_ai_title_description: {str(e)}")
        return f"Cronisphere Episode {episode_number}: AI-Generated News Summary", f"Welcome to Cronisphere Episode {episode_number}! In this episode, we bring you the latest AI-generated news summaries."

def get_authenticated_service():
    logger.debug("Authenticating with YouTube API")
    credentials = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            logger.debug("Refreshing expired credentials")
            credentials.refresh(Request())
        else:
            logger.debug("Generating new credentials")
            flow = InstalledAppFlow.from_client_secrets_file(
                '/Users/alessandrocarli/Programming/CursorProjects/creaitcast/creaitcast/Config_files/client_secret.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    logger.debug("Authentication successful")
    return build('youtube', 'v3', credentials=credentials)

def add_video_to_playlist(youtube, video_id, playlist_id):
    logger.debug(f"Attempting to add video {video_id} to playlist {playlist_id}")
    try:
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        )
        response = request.execute()
        logger.info(f"Video added to playlist {playlist_id} successfully.")
        print(f"Video added to playlist: {playlist_id}")
    except HttpError as e:
        logger.error(f"An error occurred when adding video to playlist: {str(e)}")


def upload_video(youtube, title, description, file_path, playlist_id, category="22", privacy_status="public"):
    logger.debug(f"Attempting to upload video: {file_path}")
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }

    media = MediaFileUpload(file_path, resumable=True)

    try:
        logger.debug("Initiating video upload")
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        response = request.execute()
        video_id = response['id']
        video_link = f"https://youtu.be/{video_id}"
        logger.info(f"Video uploaded successfully. Video ID: {video_id}")
        logger.info(f"Video link: {video_link}")
        print(f"Video uploaded successfully. Link: {video_link}")
        
        # Add video to playlist after successful upload
        if playlist_id:
            add_video_to_playlist(youtube, video_id, playlist_id)
        
        return video_link
    except HttpError as e:
        logger.error(f"An HTTP error occurred: {e.resp.status} {e.content}")
        if e.resp.status == 403 and "quotaExceeded" in str(e):
            logger.error("YouTube API quota exceeded. Please wait and try again later or use a different project.")
        raise

def main(podcast_number, num_articles):
    logger.debug(f"Starting upload process for podcast {podcast_number}")
    script_path = f"output/podcast_{podcast_number}/scripts/podcast_script.txt"
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            podcast_text = f.read()
        logger.debug(f"Podcast text content (first 200 characters): {podcast_text[:200]}")

        logger.debug("Podcast script read successfully")

        title, description = generate_ai_title_description(podcast_text, podcast_number)
        logger.debug(f"{title} {description}")
        
        if not title or not description:
            logger.warning("Failed to generate AI title and description. Using default values.")
            title = f"Cronisphere Episode {podcast_number}: AI-Generated News Summary"
            description = podcast_text[:1000] + "..."
    except Exception as e:
        logger.error(f"Error reading script or generating title/description: {str(e)}")
        return

    youtube = get_authenticated_service()
    
    video_path = f"output/podcast_{podcast_number}/video/episode{podcast_number}.mp4"
    
    if not os.path.exists(video_path):
        logger.error(f"Error: Video file not found at {video_path}")
        return

    try:
        video_link = upload_video(youtube, title, description, video_path, playlist_id="PLqoUA98Wnrxo-HLn3z4DZSbSp7tUXMSZJ")
        logger.info(f"Upload process completed. Video link: {video_link}")
        logger.info(f"Upload process completed. Video link: {title}  {description} ")
        print(title)
        print(description)
    except HttpError as e:
        if e.resp.status == 403 and "quotaExceeded" in str(e):
            logger.error("YouTube API quota exceeded. Please wait and try again later or use a different project.")
        else:
            logger.error(f"An error occurred during video upload: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 6_upload_to_youtube.py <podcast_number> <num_articles>")
        sys.exit(1)
    
    podcast_number = int(sys.argv[1])
    num_articles = int(sys.argv[2])
    main(podcast_number, num_articles)