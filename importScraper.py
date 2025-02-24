from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

sys.stdout.reconfigure(encoding='utf-8')

def setup_driver():
    """Creates and returns a headless Chrome WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")  
    chrome_options.add_argument("--window-size=1920x1080")  
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-infobars")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def duckduckgo_search(query, num_results=5):
    """Searches DuckDuckGo and returns a list of top result links."""
    driver = setup_driver()
    driver.get("https://duckduckgo.com/")

    search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "q")))
    search_box.send_keys(query + " news")  
    search_box.send_keys(Keys.RETURN)

    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-testid='result-title-a']")))

    results = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a']")
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

def fetch_news_articles(query, num_results=3, max_workers=3):
    """Fetches news articles based on a query."""
    results = duckduckgo_search(query, num_results)
    scraped_articles = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_link = {executor.submit(scrape_article, link): link for link in results}

        for future in as_completed(future_to_link):
            try:
                scraped_articles.append(future.result(timeout=20))
            except:
                scraped_articles.append(f"Failed to fetch: {future_to_link[future]}\nEOA\n")

    return "\n".join(scraped_articles)

