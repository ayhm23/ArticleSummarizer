# ArticleSummarizer


## Clear
This project automates news scraping, summarization, and publishing on WordPress. It integrates web scraping, AI-based text summarization, image generation, and database management.

## Build
### Prerequisites
Ensure you have the following installed:
- Python 3.x
- Selenium and WebDriver
- PostgreSQL
- Google API credentials (for Google Sheets integration)

Install dependencies:
bash
pip install selenium webdriver-manager gspread google-auth diffusers torch psycopg2 ollama wordpress-xmlrpc pillow


## Run
### Running the Scraper
To fetch news articles:
bash
python cronscript.py

Or using DuckDuckGo search:
bash
python importScraper.py


### Processing & Summarization
To summarize and extract metadata:
bash
python p4.py

Or alternatively:
bash
python search.py


### Posting to WordPress
Articles are posted automatically after processing. Ensure WordPress credentials are configured in wordpressfunctions.py.

## Deploy
### Google Sheets Integration
- Update service_account.json with valid Google API credentials.
- Retrieve the latest responses using:
bash
python form.py


### WordPress Configuration
- Set WP_URL, WP_USER, and WP_PASSWORD in wordpressfunctions.py.
- Modify PostgreSQL details in p4.py and search.py as needed.

### Database Setup
To initialize the database:
bash
psql -U <your_user> -d <your_db> -f setup.sql


## License
This project is for internal use. Unauthorized distribution of credentials is strictly prohibited.
# News Aggregation & Auto-Publishing System

A automated pipeline that scrapes news articles, generates AI summaries/SEO metadata, creates AI images, and publishes to WordPress.

## Components
- *Google Sheets Trigger*: Check for new user queries
- *Web Scrapers*: HT & DuckDuckGo news scraping
- *AI Processing*: Summarization & SEO optimization (Mistral via Ollama)
- *Image Generation*: Stable Diffusion integration
- *WordPress Publisher*: Auto-post with images/categories
- *PostgreSQL*: Store processed articles

## Prerequisites
1. Python 3.9+
2. PostgreSQL 14+
3. Ollama (with Mistral model)
4. WordPress site with XML-RPC enabled
5. Google Service Account credentials
6. Stable Diffusion dependencies (CUDA if using GPU)

## Installation
```bash

# Clone repo
git clone https://github.com/yourusername/news-automation.git
cd news-automation

# Install Python dependencies
pip install -r requirements.txt

# Set up Ollama
ollama pull mistral

# Configure PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE news_db;"
sudo -u postgres psql -c "CREATE USER news_admin WITH PASSWORD 'securepassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE news_db TO news_admin;"
