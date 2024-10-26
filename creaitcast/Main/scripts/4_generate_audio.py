import sys
import os
import asyncio
import edge_tts
from pathlib import Path
from pydub import AudioSegment

async def text_to_speech_chunk(text, filename, voice="en-US-ChristopherNeural"):
    """Convert a chunk of text to speech"""
    try:
        tts = edge_tts.Communicate(text=text, voice=voice)
        await tts.save(filename)
    except Exception as e:
        print(f"Error processing chunk: {e}")
        raise

def merge_audio_files(input_files, output_file):
    """Merge multiple audio files into one"""
    combined = AudioSegment.empty()
    for file in input_files:
        audio = AudioSegment.from_mp3(file)
        combined += audio
    combined.export(output_file, format="mp3")

async def text_to_speech(text, filename='output.mp3', voice="en-US-ChristopherNeural", chunk_size=2000):
    """Convert text to speech, splitting into chunks if necessary"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Split text into chunks (at sentence boundaries)
        chunks = []
        current_chunk = ""
        
        for sentence in text.replace('\n', ' ').split('. '):
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + '. '
            else:
                chunks.append(current_chunk)
                current_chunk = sentence + '. '
        if current_chunk:
            chunks.append(current_chunk)
        
        # Process each chunk
        chunk_files = []
        tasks = []
        
        for i, chunk in enumerate(chunks):
            chunk_file = f"{filename}.chunk{i}.mp3"
            chunk_files.append(chunk_file)
            tasks.append(text_to_speech_chunk(chunk, chunk_file, voice))
        
        # Process all chunks concurrently
        await asyncio.gather(*tasks)
        
        # Merge chunks if there are multiple
        if len(chunk_files) > 1:
            merge_audio_files(chunk_files, filename)
            # Clean up chunk files
            for chunk_file in chunk_files:
                os.remove(chunk_file)
        elif len(chunk_files) == 1:
            # If there's only one chunk, just rename it
            os.rename(chunk_files[0], filename)
            
        print(f"Audio file saved as {filename}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

async def main(podcast_number, num_articles):
    input_file = f"output/podcast_{podcast_number}/scripts/podcast_script.txt"
    output_file = f"output/podcast_{podcast_number}/audio/episode{podcast_number}.mp3"
    
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Script file not found: {input_file}")
            
        with open(input_file, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # You can customize the voice here
        # voice = "it-IT-IsabellaNeural" #"en-US-ChristopherNeural"  # Male voice
        voice = "en-US-ChristopherNeural"  # Male voice
        
        await text_to_speech(script_content, filename=output_file, voice=voice)
        print(f"Generated audio for podcast {podcast_number}")
        
    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 4_generate_audio.py <podcast_number> <num_articles>")
        sys.exit(1)
    
    podcast_number = int(sys.argv[1])
    num_articles = int(sys.argv[2])
    
    asyncio.run(main(podcast_number, num_articles))