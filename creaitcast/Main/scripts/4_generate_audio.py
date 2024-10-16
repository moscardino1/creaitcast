import sys
import os
from gtts import gTTS

def text_to_speech(text, lang='en', filename='output.mp3'):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(filename)
        print(f"Audio file saved as {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main(podcast_number, num_articles):
    input_file = f"output/podcast_{podcast_number}/scripts/podcast_script.txt"
    output_file = f"output/podcast_{podcast_number}/audio/episode{podcast_number}.mp3"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        text_to_speech(script_content, filename=output_file)
        print(f"Generated audio for podcast {podcast_number}")
    except Exception as e:
        print(f"Error generating audio: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 4_generate_audio.py <podcast_number> <num_articles>")
        sys.exit(1)
    
    podcast_number = int(sys.argv[1])
    num_articles = int(sys.argv[2])
    main(podcast_number, num_articles)