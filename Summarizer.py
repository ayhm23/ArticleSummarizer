import ollama
import psycopg2
from psycopg2 import sql
# import importScraper
import cronscript
import wordpressfunctions
from concurrent.futures import ThreadPoolExecutor

import re
import torch
import os
os.environ["XFORMERS_DISABLED"] = "1"
from datetime import datetime
from psycopg2 import sql
from diffusers import StableDiffusionPipeline

MAX_PROMPT_LENGTH = 250
IMAGE_SIZE = 180  # Reduce to 256 if you have < 8GB VRAM
SD_MODEL = "stabilityai/stable-diffusion-2-1-base"



# PostgreSQL Connection Details
DB_NAME = "news_db"
DB_USER = "news_admin"
DB_PASSWORD = "securepassword"
DB_HOST = "localhost"
DB_PORT = "5432"

def connect_db():
    """Establish connection to PostgreSQL."""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

def create_table():
    """Create the summaries table with SEO fields if it doesn't exist."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id SERIAL PRIMARY KEY,
            headline TEXT NOT NULL,
            summary TEXT NOT NULL,
            seo_title TEXT NOT NULL,
            meta_description TEXT NOT NULL,
            key_phrases TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ PostgreSQL table ready!")

def generate_image_prompt(summary):
    """Structured prompt engineering for better results"""
    structured_template = """Create an image prompt using this format:
    [Subject/Activity] in/at [Location], [Art Style], [Camera Details], [Cultural Context], [Mood]
    
    Rules:
    - Be specific about elements
    - Use photojournalism terms
    - Avoid abstract concepts
    - No text/letters
    
    Summary: {summary}
    """
    
    response = ollama.chat(
        model="mistral",
        messages=[{
            "role": "user", 
            "content": structured_template.format(summary=summary)
        }]
    )
    
    # Post-process the response
    prompt = response['message']['content'].strip()
    prompt = re.sub(r'(Image:|Prompt:|\n)', ' ', prompt)  # Clean formatting
    return f"Professional press photo, {prompt}"[:MAX_PROMPT_LENGTH]

def generate_image(prompt, headline):
    """Generate image with memory optimizations."""
    print(prompt)
    if not prompt:
        return None

    try:
        # Initialize pipeline
        pipe = StableDiffusionPipeline.from_pretrained(
            SD_MODEL,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        
        # Memory optimizations
        device = "cuda" if torch.cuda.is_available() else "cpu"
        pipe = pipe.to(device)
        pipe.enable_attention_slicing()
        
        if device == "cuda":
            torch.cuda.empty_cache()

        # Generate image
        image = pipe(
            prompt,
            height=IMAGE_SIZE,
            width=IMAGE_SIZE,
            num_inference_steps=25
        ).images[0]

        # Create filename
        clean_headline = re.sub(r'\W+', '_', headline)[:20]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"news_{timestamp}_{clean_headline}.png"
        image.save(filename)
        return filename

    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return None

def summarize_text(headline, text):
    """Summarizes a news article and generates SEO elements using Mistral via Ollama."""
    prompt = f"""
    STRUCTURED RESPONSE REQUIRED
    Provide the following sections EXACTLY as shown below, separated by '===':

    === Summary ===
    [min 8-10 sentence summary. Concise and factual.]

    === SEO Title ===
    [Generate an engaging SEO title under 60 characters, include keywords and form a complete, compelling sentence.]

    === Meta Description ===
    [Brief description under 160 characters. Include keywords.]

    === Key Phrases ===
    [Comma-separated list of 3-5 key phrases.]

    Article Analysis
    Headline: {headline}
    Text: {text}

    Rules
    - Ignore advertisements.
    - Follow the format EXACTLY.
    """
    print("Sending request to Ollama...\n")
    response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
    full_response = response['message']['content']
    print("Raw Ollama Response:\n", full_response)

    # Improved parsing logic
    sections = {}
    current_section = None
    lines = full_response.split('\n')
    
    for line in lines:
        stripped_line = line.strip()
        
        # Detect section headers like "=== Summary ==="
        if stripped_line.startswith("===") and stripped_line.endswith("==="):
            current_section = stripped_line.replace("===", "").strip()
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(stripped_line)

    # Convert lists to strings
    for key in sections:
        sections[key] = "\n".join(sections[key]).strip()

    print("Parsed Sections:", sections)

    # Validate all required sections exist
    required = ["Summary", "SEO Title", "Meta Description", "Key Phrases"]
    for section in required:
        if section not in sections:
            print(f"⚠️ Missing section: {section}")
            return None, None, None, None

    # Extract content
    summary = sections["Summary"].replace("HT@100", "").strip()
    seo_title = sections["SEO Title"].replace("HT@100", "").strip()
    meta_description = sections["Meta Description"].replace("HT@100", "").strip()

    # key_phrases = [
    #     phrase.strip() 
    #     for phrase in sections["Key Phrases"].split(',') 
    #     if phrase.strip() != "HT@100"  # Exclude exact matches
    # ]
    key_phrases = [
    phrase.lstrip(' -').strip()  # Remove leading hyphens/spaces first
    for phrase in sections["Key Phrases"].split(',') 
    if phrase.strip() != "HT@100"  # Exclude exact matches after cleanup
]

    print("\n✅ Parsed Successfully:")
    print("Summary:", summary)
    print("SEO Title:", seo_title)
    print("Meta Description:", meta_description)
    print("Key Phrases:", key_phrases)

    return summary, seo_title, meta_description, key_phrases

def save_to_db(headline, summary, seo_title, meta_description, key_phrases):
    print(f"💾 Attempting to save: {headline}, {summary}, {seo_title}, {meta_description}, {key_phrases}")
    conn = connect_db()
    cursor = conn.cursor()
    key_phrases_str = ','.join(key_phrases)
    
    try:
        cursor.execute(
            sql.SQL("INSERT INTO summaries (headline, summary, seo_title, meta_description, key_phrases) VALUES (%s, %s, %s, %s, %s)"),
            (headline, summary, seo_title, meta_description, key_phrases_str)
        )
        conn.commit()
        print(f"✅ Summary for '{headline}' saved to PostgreSQL!")
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
    finally:
        cursor.close()
        conn.close()

# def process_articles_combined(headlines, bodies):
#     """Summarize multiple articles and save with SEO elements."""
#     combined_headline = " ".join(headlines)
#     combined_body = "\n".join(bodies)

#     # Truncate the combined body to 250 words
#     words = combined_body.split()
#     if len(words) > 400:
#         truncated_body = " ".join(words[:400]) + "... [truncated]"
#         combined_body = truncated_body
#         print("⚠️ Combined text exceeded 250 words. Truncated.")

#     summary, seo_title, meta_description, key_phrases = summarize_text(combined_headline, combined_body)
    
#     if summary is None:
#         print("⚠️ Skipping due to incomplete response")
#         return
    
#     save_to_db(combined_headline, summary, seo_title, meta_description, key_phrases)
#     return  seo_title , summary , key_phrases

# def main():
#     """Main function to scrape, summarize, and store news articles in parallel."""
#     create_table()  # Ensure DB table exists with new schema

#     # Scrape the news
#     # query = "virat kohli"
#     # scraped_news = importScraper.fetch_news_articles(query)
#     scraped_news

#     if not scraped_news:
#         print("❌ No valid articles found from scraping")
#         return

#     # Split the scraped news into individual articles
#     articles = scraped_news.strip().split("EOA")  # Split articles using 'EOA'

#     if len(articles) < 1:
#         print("❌ NO articles found. Skipping summary generation.")
#         return

#     # Extract headlines and bodies for all articles
#     headlines = []
#     bodies = []
#     for article in articles[:3]:  # Only take the first 3 articles
#         print(article)
#         lines = article.strip().split("\n", 1)  # Extract headline and body
#         if len(lines) < 2:
#             continue
#         headlines.append(lines[0].replace("Article", "").strip())  
#         bodies.append(lines[1].strip())  

#     # Process the combined articles in parallel
#     with ThreadPoolExecutor() as executor:
#         future = executor.submit(process_articles_combined, headlines, bodies)
#         title, summary ,keywords= future.result()  # Extract results here

#     print("🚀 All scraped news summaries stored in PostgreSQL!")
#     wordpressfunctions.post_to_wordpress(title, summary,keywords)

    
# ... (previous imports remain the same)
# import cronscript  # Add this line

# from concurrent.futures import ThreadPoolExecutor

def process_single_article(headline, body):
    """Summarize a single article and save it with SEO elements."""
    
    if not headline or not body:
        print("⚠️ Missing headline or body. Skipping processing.")
        return
    
    # Truncate the body to 400 words if necessary
    words = body.split()
    if len(words) > 400:
        truncated_body = " ".join(words[:400]) + "... [truncated]"
        body = truncated_body
        print("⚠️ Article body exceeded 400 words. Truncated.")

    # Generate summary, SEO title, meta description, and key phrases
    summary, seo_title, meta_description, key_phrases = summarize_text(headline, body)
    
    
    
    # Generate image
    image_prompt = generate_image_prompt(summary)
    image_path = generate_image(image_prompt, headline)

    if summary is None:
        print("⚠️ Skipping due to incomplete response")
        return None, None, None, None
    
    # Save processed data to the database
    save_to_db(headline, summary, seo_title, meta_description, key_phrases)
    
    return seo_title, summary, key_phrases, image_path


def process_and_post_article(article):
    """
    Process a single article and post it to WordPress.
    
    Args:
        article (str): The raw article string containing headline and body.
    """
    # Split the article into headline and body based on the first newline.
    parts = article.split("\n", 1)
    if len(parts) < 2:
        print(f"❌ Invalid article format: {article[:50]}...")
        return
    
    # Remove the "Article: " prefix from the headline.
    headline = parts[0].replace("Article: ", "").strip()
    # Split the remaining text by the "EOA" marker to extract the body.
    body = parts[1].split("EOA")[0].strip()
    
    # Process the article to extract the title, summary, and keywords.
    title, summary, keywords, image_path = process_single_article(headline, body)
    
    print(f"Image path type: {type(image_path)}, value: {image_path}")

    if None in (title, summary, image_path, keywords):
        print("Error: Missing required fields")
    else:
        # Post the processed article to WordPress.
        wordpressfunctions.post_with_image(title, summary, image_path, keywords)

def main():
    """Main function to fetch, process, and post articles."""
    create_table()  # Ensure the database table exists.
    
    # Fetch articles using your cron script.
    scraped_articles = cronscript.get_articles()
    print("no of articles : "+ str(len(scraped_articles)) +"\n")
    if not scraped_articles:
        print("❌ No articles scraped.")
        return
    
    # Process and post each article concurrently.
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(process_and_post_article, scraped_articles))
    
    print("🚀 All articles processed and posted to WordPress!")

    
if __name__ == "__main__":
    main()
