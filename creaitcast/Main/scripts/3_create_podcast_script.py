import sys
import os

def create_introduction(podcast_number):
    return f"""Welcome to podcast number {podcast_number} of our AI-generated news summary.
Let's dive into the summaries of our top stories."""

def create_conclusion():
    return """That concludes our AI-generated news summary for today.
Thanks for listening, and stay tuned for our next episode."""

def main(podcast_number, num_articles):
    input_folder = f"output/podcast_{podcast_number}/summaries"
    output_folder = f"output/podcast_{podcast_number}/scripts"
    output_file = os.path.join(output_folder, "podcast_script.txt")

    script_content = create_introduction(podcast_number) + "\n\n"

    for i in range(1, num_articles + 1):
        summary_file = os.path.join(input_folder, f"summary_{i}.txt")
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            title = content.split('\n')[0].replace("Title: ", "")
            summary = content.split('Summary:\n')[1]

            script_content += f"Our next story is titled: {title}\n"
            script_content += f"{summary}\n\n"

        except Exception as e:
            print(f"Error processing summary {i}: {str(e)}")

    script_content += create_conclusion()

    os.makedirs(output_folder, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(script_content)

    print(f"Created podcast script for podcast {podcast_number}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 3_create_podcast_script.py <podcast_number> <num_articles>")
        sys.exit(1)
    
    podcast_number = int(sys.argv[1])
    num_articles = int(sys.argv[2])
    main(podcast_number, num_articles)