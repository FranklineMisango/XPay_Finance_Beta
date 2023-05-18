import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
from transformers import PegasusTokenizer, PegasusForConditionalGeneration
from transformers import pipeline

#Calling the sentiment analysis to perform sentiment labelling for the summaries
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
model_name = "distilbert-base-uncased-finetuned-sst-2-english"
model_revision = "af0f99b"
model = AutoModelForSequenceClassification.from_pretrained(model_name, revision=model_revision)
tokenizer = AutoTokenizer.from_pretrained(model_name, revision=model_revision)
sentiment = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)

#Searching for the stock tickers url 
def search_for_stock_news_urls(ticker, source):
    if source == "Bloomberg":
        search_url = f"https://www.google.com/search?q=bloomberg+{ticker}&tbm=nws"
    elif source == "Yahoo":
        search_url = f"https://www.google.com/search?q=yahoo+finance+{ticker}&tbm=nws"
    elif source == "Investopedia":
        search_url = f"https://www.google.com/search?q=investopedia+{ticker}&tbm=nws"
    elif source == "Google Finance":
        search_url = f"https://www.google.com/search?q=google+finance++{ticker}&tbm=nws"
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
    elif source == "Google Finance":
        atags = soup.find_all('a')
    else:
        return None

    hrefs = [link['href'] for link in atags]
    return hrefs

#Strip out the unwanted URLs--> policies,accounts, preferences etc
excluded_list = ['maps', 'policies', 'preferences', 'support', 'accounts']
def strip_unwanted_urls(urls, excluded_list):
    final_val = []
    for url in urls:
        if 'https://' in url and not any(excluded_word in url for excluded_word in excluded_list):
            res = re.findall(r'(https?://\S+)', url)[0].split('&')[0]
            final_val.append(res)
    return list(set(final_val))

#Seach and scrape cleaned URLs
def scrape_and_process(urls):
    ARTICLES = []
    for url in urls:
        try:
            headers = {}
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            paragraphs = soup.find_all('p')
            text = [paragraph.text for paragraph in paragraphs]
            words = ''.join(text).split(' ')[:400]
            ARTICLE = ''.join(words)
            ARTICLES.append(ARTICLE)
        except:
            print(f"Error occurred while scraping {url}")
            continue
    return ARTICLES

# Define the summarization pipeline
def summarize_all_articles(articles):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    summaries = []
    for article in articles:
        # Use the summarizer pipeline to generate a summary
        summary = summarizer(article, max_length=120, min_length=30, do_sample=False)[0]['summary_text']
        summaries.append(summary)
    return summaries

stop_words = [
    'Ourengineersareworkingquicklytoresolvetheissue. Thankyouforyourpatience. Back to Mail Online home. back to the page you came from.',
    ' PleasemakesureyourbrowsersupportsJavaScriptandcookiesandthatyouarenotblockingthemfromloading. Tocontinue,pleaseclicktheboxbelowtoletusknowyou renotarobot.',
    '2023-私隱權政策-條款. ©2023. www.japanewspaper.com'
]
def perform_sentiment_analysis(summaries, monitored_tickers):
    scores = {
        ticker: sentiment(summaries[ticker])
        for ticker in monitored_tickers
    }
    return scores

def main():
    st.title('Xpay Research GPT : Level I ')
    st.image('images/cover.png')

    num_tickers = st.number_input("Enter the number of stock tickers you want to monitor:", value=1, min_value=1, step=1)
    monitored_tickers = []
    for i in range(num_tickers):
        ticker = st.text_input(f"Enter the company's stock ticker {i+1}:")
        monitored_tickers.append(ticker)

    sources = ["Bloomberg", "Yahoo Finance", "Investopedia", "Google Finance"]
    source_choice = st.selectbox("Select the source you want to use:", sources)
    predict_button = st.button("Predict")

    if predict_button:
        raw_urls = {ticker: search_for_stock_news_urls(ticker, source_choice) for ticker in monitored_tickers}
        cleaned_urls = {ticker:strip_unwanted_urls(raw_urls[ticker], excluded_list) for ticker in monitored_tickers}
        articles = {ticker:scrape_and_process(cleaned_urls[ticker]) for ticker in monitored_tickers}
        summaries = {ticker:summarize_all_articles(articles[ticker]) for ticker in monitored_tickers}

        # Perform sentiment analysis
        scores = perform_sentiment_analysis(summaries, monitored_tickers)

        # Display results
        for ticker in scores:
            st.subheader(f"Sentiment analysis for {ticker}:")
            for i, score in enumerate(scores[ticker]):
                summary = summaries[ticker][i]
                if any(word in summary for word in stop_words) or re.match(r'^\s*$', summary):
                    continue  # Skip if the sentiment contains stop words or phrases, or is blank

                negative_count = sum(1 for score in scores[ticker] if score['label'] == 'NEGATIVE')

                if negative_count > 5:
                    message = f"The model finds that stock {ticker} is not doing well currently. We recommend that you don't buy for short holding."
                elif negative_count == 5:
                    message = f"The model generates a neutral view on stock {ticker}, further organic research is needed"
                else:
                    message = f"The model finds that stock {ticker} is good to buy for the short term. Contact our brokers below to buy."

                st.warning(message)
                querry_button = st.button("See Why")
                if querry_button:
                    st.write(f"{i+1}. Summary: {summary}")
                    st.write(f"   Score: {score['score']}, Label: {score['label']}")

if __name__ == '__main__':
    main()