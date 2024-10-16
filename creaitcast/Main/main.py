import os
import subprocess
import sys

def create_folders(podcast_number):
    base_path = f"output/podcast_{podcast_number}"
    folders = ["articles", "summaries", "scripts", "audio", "video"]
    for folder in folders:
        os.makedirs(os.path.join(base_path, folder), exist_ok=True)

def run_script(script_name, podcast_number, num_articles):
    script_path = os.path.join("scripts", script_name)
    result = subprocess.run([sys.executable, script_path, str(podcast_number), str(num_articles)], capture_output=True, text=True)
    print(f"Output from {script_name}:")
    print(result.stdout)
    if result.stderr:
        print(f"Error output from {script_name}:")
        print(result.stderr)
    if result.returncode != 0:
        print(f"Script {script_name} failed with return code {result.returncode}")
        return False
    return True

def main():
    podcast_number = int(input("Enter the podcast number: "))
    num_articles = int(input("Enter the number of articles to process: "))

    create_folders(podcast_number)

    steps = [
        # "1_parse_articles.py",
        # "2_summarize_articles.py",
        # "3_create_podcast_script.py",
        # "4_generate_audio.py",
        # "5_create_video.py",
        # "6_upload_to_youtube.py"
    ]

    for step in steps:
        print(f"\nRunning {step}...")
        if not run_script(step, podcast_number, num_articles):
            print(f"Error occurred in {step}. Stopping process.")
            break

    print("\nPodcast generation process completed.")

if __name__ == "__main__":
    main()