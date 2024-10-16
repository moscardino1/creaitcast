import os
import sys
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import random
from collections import Counter

def simple_tokenize(text):
    # Remove punctuation and convert to lowercase
    text = ''.join(c.lower() for c in text if c.isalnum() or c.isspace())
    return text.split()

def extract_keywords(text, num_keywords=5):
    tokens = simple_tokenize(text)
    # Define a simple list of stop words
    stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
    keywords = [word for word in tokens if word not in stop_words]
    
    keyword_freq = Counter(keywords)
    common_keywords = [word for word, _ in keyword_freq.most_common(num_keywords)]
    
    return common_keywords

def generate_images(keywords, num_images=10, output_folder=''):
    images = []
    for i in range(num_images):
        keyword = random.choice(keywords)
        print(f"Generating image for: {keyword}")
        
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        img = Image.new('RGB', (640, 480), color=color)
        
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        left, top, right, bottom = draw.textbbox((0, 0), keyword, font=font)
        text_width = right - left
        text_height = bottom - top
        position = ((640-text_width)/2, (480-text_height)/2)
        draw.text(position, keyword, fill=(255-color[0], 255-color[1], 255-color[2]), font=font)
        
        image_path = os.path.join(output_folder, f"generated_image_{i}.png")
        img.save(image_path)
        images.append(image_path)
    return images

def convert_audio_to_video(input_audio, output_video, sample_text, image_folder):
    audio = AudioFileClip(input_audio)
    
    keywords = extract_keywords(sample_text)
    image_paths = generate_images(keywords, output_folder=image_folder)
    
    clips = []
    duration_per_image = audio.duration / len(image_paths)
    for img_path in image_paths:
        img_clip = ImageClip(img_path).set_duration(duration_per_image)
        clips.append(img_clip)
    
    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(audio)
    video = video.set_fps(24)
    
    video.write_videofile(output_video, codec='libx264', audio_codec='aac')
    print(f"Converted {input_audio} to {output_video}")

def main(podcast_number, num_articles):
    input_audio = f"output/podcast_{podcast_number}/audio/episode{podcast_number}.mp3"
    output_video = f"output/podcast_{podcast_number}/video/episode{podcast_number}.mp4"
    script_file = f"output/podcast_{podcast_number}/scripts/podcast_script.txt"
    image_folder = f"output/podcast_{podcast_number}/video/images"
    
    os.makedirs(image_folder, exist_ok=True)
    
    with open(script_file, 'r', encoding='utf-8') as f:
        sample_text = f.read()
    
    convert_audio_to_video(input_audio, output_video, sample_text, image_folder)
    print(f"Created video for podcast {podcast_number}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 5_create_video.py <podcast_number> <num_articles>")
        sys.exit(1)
    
    podcast_number = int(sys.argv[1])
    num_articles = int(sys.argv[2])
    main(podcast_number, num_articles)