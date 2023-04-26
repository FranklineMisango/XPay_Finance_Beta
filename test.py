#Building a News and Sentiment Pipleline
#Test with company stock names --Edited to user preference
#The model asks which tinkers you wanna monitor and how much
#You can also edit the search URL to use expedia or Bloomberg finance
#Search for stock news using Google and Yahoo Finance
#TODO--> Figure out how to allow a universal Web scrapping instead of relying solely on Yahoo finance. ie investopedia, Bloomberg LP etc
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def search_for_stock_news_urls(ticker, source):
  if source == "Bloomberg":
    search_url = f"https://www.google.com/search?q=bloomberg+{ticker}&tbm=nws"
  elif source == "Yahoo":
    search_url = f"https://www.google.com/search?q=yahoo+finance+{ticker}&tbm=nws"
  elif source == "Investopedia":
    search_url = f"https://www.google.com/search?q=investopedia+{ticker}&tbm=nws"
  else:
    return None
  
  r = requests.get(search_url)
  soup = BeautifulSoup(r.text, 'html.parser')
  if source == "Bloomberg":
    atags = soup.find_all('a')
  elif source == "Yahoo":
    atags = soup.find_all('a')
  elif source == "Investopedia":
    atags = soup.find_all('a')
  else:
    return None
  
  hrefs = [link['href'] for link in atags]
  return hrefs

num_tickers = int(input("Enter the number of stock tickers you want to monitor: "))
monitored_tickers = []
for i in range(num_tickers):
  ticker = input(f"Enter the company's stock ticker {i+1}: ")
  monitored_tickers.append(ticker)

sources = ["Bloomberg", "Yahoo", "Investopedia"]
source_choice = input(f"Enter the source you want to use ({', '.join(sources)}), or type 'all': ")

if source_choice.lower() == "all":
  raw_urls = {}
  for ticker in monitored_tickers:
    raw_urls[ticker] = []
    for source in sources:
      urls = search_for_stock_news_urls(ticker, source)
      if urls is not None:
        raw_urls[ticker].extend(urls)
else:
  raw_urls = {ticker: search_for_stock_news_urls(ticker, source_choice) for ticker in monitored_tickers}

print(raw_urls)

#Strip out the unwanted URLs--> policies,accounts, preferences etc
excluded_list = ['maps', 'policies', 'preferences', 'support', 'accounts']
def strip_unwanted_urls(urls, excluded_list):
    final_val = []
    for url in urls:
        if 'https://' in url and not any(excluded_word in url for excluded_word in excluded_list):
            res = re.findall(r'(https?://\S+)', url)[0].split('&')[0]
            final_val.append(res)
    return list(set(final_val))

cleaned_urls = {ticker:strip_unwanted_urls(raw_urls[ticker], excluded_list) for ticker in monitored_tickers}
cleaned_urls

#Seach and scrape cleaned URLs
#Seach and scrape cleaned URLs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# Search and scrape cleaned URLs
def scrape_and_process(urls):
    ARTICLES = []
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--headless")
    service = Service('chromedriver.exe') # replace with the path to your chromedriver executable
    driver = webdriver.Chrome(service=service, options=options)

    for url in urls:
        driver.get(url)
        try:
            element_present = EC.presence_of_element_located((By.TAG_NAME, 'p'))
            WebDriverWait(driver, timeout=5).until(element_present)
        except TimeoutException:
            print(f"Timed out waiting for page to load: {url}")
            continue
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        paragraphs = soup.find_all('p')
        text = [paragraph.text for paragraph in paragraphs]
        words = ''.join(text).split(' ')[:400]
        ARTICLE = ''.join(words)
        ARTICLES.append(ARTICLE)
    driver.quit()
    return ARTICLES

articles = {ticker:scrape_and_process(cleaned_urls[ticker]) for ticker in monitored_tickers}
print(articles)

