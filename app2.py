import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
from transformers import PegasusTokenizer, PegasusForConditionalGeneration
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import concurrent.futures

# Move import statements to the top

# ...

# Initialize sentiment analysis pipeline outside the main function
model_name = "distilbert-base-uncased-finetuned-sst-2-english"
model_revision = "af0f99b"
model = AutoModelForSequenceClassification.from_pretrained(model_name, revision=model_revision)
tokenizer = AutoTokenizer.from_pretrained(model_name, revision=model_revision)
sentiment = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)

# ...

# Define the summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# ...


def search_for_stock_news_urls(ticker, source):
    if source == "Bloomberg":
        search_url = f"https://www.google.com/search?q=bloomberg+{ticker}&tbm=nws"
    elif source == "Yahoo Finance":
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
    elif source == "Yahoo Finance":
        atags = soup.find_all('a')
    elif source == "Investopedia":
        atags = soup.find_all('a')
    elif source == "Google Finance":
        atags = soup.find_all('a')
    else:
        return None

    hrefs = [link['href'] for link in atags]
    return hrefs

excluded_list = ['maps', 'policies', 'preferences', 'support', 'accounts']
def strip_unwanted_urls(urls, excluded_list):
    if urls is None:
        return []
    final_val = []
    for url in urls:
        if 'https://' in url and not any(excluded_word in url for excluded_word in excluded_list):
            res = re.findall(r'(https?://\S+)', url)[0].split('&')[0]
            final_val.append(res)
    return list(set(final_val))

def scrape_and_process(url):
    try:
        headers = {}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        text = [paragraph.text for paragraph in paragraphs]
        words = ''.join(text).split(' ')[:400]
        article = ''.join(words)
        return article
    except Exception as e:
        print(f"Error occurred while scraping {url}: {str(e)}")
        return None
    
def summarize_all_articles(articles):
    if articles is None:
        return []  # Return an empty list if articles is None

    summaries = []
    for article in articles:
        # Perform summarization for each article and append the summary to the list
        summary = summarizer(article, max_length=120, min_length=30, do_sample=False)
        if len(summary) > 0:
            summaries.append(summary[0]['summary_text'])
    
    return summaries


def perform_sentiment_analysis(summaries, monitored_tickers):
    scores = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_ticker = {executor.submit(sentiment, summary): ticker for ticker, summary in summaries.items()}
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                score = future.result()
                scores[ticker] = score
            except Exception as e:
                print(f"Error occurred during sentiment analysis for {ticker}: {str(e)}")
    return scores

# ...

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

    stop_words = [
    'Ourengineersareworkingquicklytoresolvetheissue. Thankyouforyourpatience. Back to Mail Online home. back to the page you came from.',
    ' PleasemakesureyourbrowsersupportsJavaScriptandcookiesandthatyouarenotblockingthemfromloading. Tocontinue,pleaseclicktheboxbelowtoletusknowyou renotarobot.',
    '2023-私隱權政策-條款. ©2023. www.japanewspaper.com'
    
    ]
    if predict_button:
        raw_urls = {ticker: search_for_stock_news_urls(ticker, source_choice) for ticker in monitored_tickers}
        cleaned_urls = {ticker:strip_unwanted_urls(raw_urls[ticker], excluded_list) for ticker in monitored_tickers}
        articles = {ticker:scrape_and_process(cleaned_urls[ticker]) for ticker in monitored_tickers}
        summaries = {ticker:summarize_all_articles(articles[ticker]) for ticker in monitored_tickers}

        scores = perform_sentiment_analysis(summaries, monitored_tickers)

        for ticker in scores:
            st.header(f"Analysis for {ticker}:")
            for i, score in enumerate(scores[ticker]):
                summary = summaries[ticker][i]
                if any(word in summary for word in stop_words) or re.match(r'^\s*$', summary):
                    continue  # Skip if the sentiment contains stop words or phrases, or is blank
                st.write(f"{i+1}. Summary: {summary}")
                summary
                st.write(f"   Score: {score['score']}, Label: {score['label']}")
            negative_count = sum(
                1 for score in scores[ticker] if score['label'] == 'NEGATIVE'
            )
            if negative_count > 5:
                st.warning(f"The model finds that stock {ticker} is not doing well currently. We recommend that you don't buy for short holding.")
            elif negative_count == 5:
                st.info(f"The model generates a neutral view on stock {ticker}, further research is needed: Bloomberg / Expedia refinement.")
            elif negative_count < 5:
                st.success(f"The model finds that stock {ticker} is good to buy for the short term. Contact our brokers to buy.") 

if __name__ == '__main__':
    main()