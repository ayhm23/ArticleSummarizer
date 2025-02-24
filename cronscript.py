from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import sys
import wordpressfunctions

sys.stdout.reconfigure(encoding='utf-8')

def setup_driver():
    """Creates and returns a headless Chrome WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Keep headless for speed
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")  
    chrome_options.add_argument("--window-size=1920x1080")  
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-infobars")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def ht_search(link, num_results=5):
    """Scrapes news links from a page."""
    driver = setup_driver()
    driver.get(link)

    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(3)  # Let JS load

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    results = driver.find_elements(By.CSS_SELECTOR, "h3 a")
    links = [result.get_attribute("href") for result in results if result.get_attribute("href")]

    driver.quit()
    return links[:num_results]

def scrape_article(link, max_wait_time=10):
    """Scrapes the article headline and text from the given link."""
    driver = setup_driver()
    driver.get(link)
    start_time = time.time()

    try:
        headline = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).text
    except:
        headline = "No headline found"

    paragraphs = driver.find_elements(By.TAG_NAME, "p")
    article_text = "\n".join([p.text for p in paragraphs])

    if time.time() - start_time > max_wait_time:
        driver.quit()
        return f"Skipped article (too slow): {link}\nEOA\n"

    driver.quit()
    return f"Article: {headline}\n{article_text}\nEOA\n"

def fetch_news_articles(articles, max_workers=3):
    """Fetches news articles based on a query."""
    scraped_articles = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_link = {executor.submit(scrape_article, link): link for link in articles}

        for future in as_completed(future_to_link):
            try:
                scraped_articles.append(future.result(timeout=20))
            except:
                scraped_articles.append(f"Failed to fetch: {future_to_link[future]}\nEOA\n")

    return scraped_articles

# List of URLs and number of results per site

# def get_articles:
#     urls = [
#         ("https://www.hindustantimes.com/india-news/", 3),
#         ("https://www.hindustantimes.com/world-news/", 2),
#         ("https://www.hindustantimes.com/sports/football", 2),
#         ("https://www.hindustantimes.com/cricket", 2),
#         ("https://www.hindustantimes.com/sports", 2),
#         ("https://www.hindustantimes.com/entertainment/music", 2),
#         ("https://www.hindustantimes.com/entertainment/", 3),
#         ("https://tech.hindustantimes.com/", 4),
#         ("https://www.hindustantimes.com/", 5)
#     ]

#     articles = []

#     # Use ThreadPoolExecutor to run searches in parallel
#     with ThreadPoolExecutor(max_workers=4) as executor:  # Adjust workers based on your CPU
#         future_to_url = {executor.submit(ht_search, url, num): (url, num) for url, num in urls}
        
#         for future in as_completed(future_to_url):
#             url, num = future_to_url[future]
#             try:
#                 links = future.result()
#                 articles.extend(links)
#             except Exception as e:
#                 articles.extend([])

#     articles = list(set((articles)))
#     scraped_articles = fetch_news_articles(articles)
# # for i in range(len(articles)):
# #     wordpressfunctions.post_to_wordpress("title", scraped_articles[i])

# ... (previous imports and functions remain the same)

def get_articles():
    """Collects articles from specified URLs and returns scraped content."""
    urls = [
        ("https://www.hindustantimes.com/india-news/", 2),
        ("https://www.hindustantimes.com/world-news/", 2),
        ("https://www.hindustantimes.com/sports/football", 1),
        ("https://www.hindustantimes.com/cricket", 1),
        ("https://www.hindustantimes.com/sports", 2),
        ("https://www.hindustantimes.com/entertainment/music", 1),
        ("https://www.hindustantimes.com/entertainment/", 1),
        ("https://tech.hindustantimes.com/", 2),
        ("https://www.hindustantimes.com/", 2)
    ]

    articles = []

    # Use ThreadPoolExecutor to run searches in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_url = {executor.submit(ht_search, url, num): (url, num) for url, num in urls}
        
        for future in as_completed(future_to_url):
            url, num = future_to_url[future]
            try:
                links = future.result()
                articles.extend(links)
            except Exception as e:
                print(f"Error fetching links from {url}: {e}")

    # Remove duplicates and scrape articles
    articles = list(set(articles))
    scraped_articles = fetch_news_articles(articles)
    # print(scrapped_articles)
    return scraped_articles
