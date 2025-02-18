import logging
import random
import time
from datetime import datetime
from flask import flash, jsonify, redirect, render_template, request, url_for
from app.config.utils import mysql, MySQLdb
from bs4 import BeautifulSoup
import requests
from newspaper import Article
import os
from googlenewsdecoder import new_decoderv1
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import queue
from threading import Lock
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class GoogleNewsScraper:
    def __init__(self, max_workers=5, batch_size=50):
        self.base_url = "https://news.google.com/search"
        self.headers = {"User-Agent": self.get_random_user_agent()}
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.article_queue = queue.Queue()
        self.db_lock = Lock()

        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=5,  # Max retry attempts
            backoff_factor=2,  # Exponential backoff
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=100, pool_maxsize=100
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Initialize cache
        self.cache = {}
        self.setup_logger()

    def setup_logger(self):
        if not os.path.exists("logs"):
            os.makedirs("logs")

        self.logger = logging.getLogger("GoogleNewsScraper")
        self.logger.setLevel(logging.DEBUG)

        handlers = [
            (logging.FileHandler("logs/scraper.log"), logging.DEBUG),
            (logging.FileHandler("logs/scraper_errors.log"), logging.ERROR),
            (logging.StreamHandler(), logging.INFO),
        ]

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        for handler, level in handlers:
            handler.setLevel(level)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    @staticmethod
    def get_random_user_agent():
        USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]
        return random.choice(USER_AGENTS)

    def fetch_with_cache(self, url):
        if url in self.cache:
            self.logger.debug(f"Cache hit for URL: {url}")
            return self.cache[url]

        self.logger.debug(f"Fetching URL: {url}")
        try:
            delay = random.uniform(1, 3)
            time.sleep(delay)
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            self.cache[url] = response.text
            return response.text
        except Exception as e:
            self.logger.error(f"Error fetching URL {url}: {e}")
            return None

    def fetch_article_content(self, url):
        try:
            self.logger.debug(f"Fetching content from: {url}")
            decoded_url_data = new_decoderv1(url, interval=2)

            if not decoded_url_data or "decoded_url" not in decoded_url_data:
                return None

            decoded_url = decoded_url_data["decoded_url"]
            article = Article(decoded_url)
            article.download()
            article.parse()

            return (
                {
                    "text": article.text,
                    "top_image": article.top_image,
                    "authors": article.authors,
                }
                if article.text
                else None
            )

        except Exception as e:
            self.logger.error(f"Error fetching content from {url}: {e}")
            return None

    def process_article(self, article, group, start_date, end_date):
        try:
            title_elem = article.find("a", class_="JtKRv")
            if not title_elem:
                return None

            date_elem = article.find("time", class_="hvbAAd")
            if not date_elem:
                return None

            datetime_str = date_elem.get("datetime", "")
            try:
                article_date = datetime.fromisoformat(
                    datetime_str.replace("Z", "+00:00")
                )
            except ValueError:
                return None

            if not (start_date <= article_date.date() <= end_date):
                return None

            link = title_elem.get("href", "")
            if link.startswith("./"):
                link = f"https://news.google.com/{link[2:]}"

            article_content = self.fetch_article_content(link)
            if not article_content:
                return None

            return {
                "title": title_elem.text.strip(),
                "link": link,
                "source": (
                    article.find("div", class_="vr1PYe").text.strip()
                    if article.find("div", class_="vr1PYe")
                    else ""
                ),
                "published_date": article_date.strftime("%Y-%m-%d"),
                "img1": (
                    article.find("img", class_="msvBD krHqHb").get("src", "")
                    if article.find("img", class_="msvBD krHqHb")
                    else ""
                ),
                "img2": article_content.get("top_image", ""),
                "group": group,
                "sentiment": "Positif",
                "type": "Online News",
                "content": article_content.get("text", ""),
                "authors": article_content.get("authors", []),
            }

        except Exception as e:
            self.logger.error(f"Error processing article: {e}")
            return None

    def save_articles_batch(self, articles):
        if not articles:
            return

        with self.db_lock:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            try:
                for article in articles:
                    cur.execute(
                        "SELECT link FROM tb_article WHERE link = %s",
                        (article["link"],),
                    )
                    if cur.fetchone():
                        cur.execute(
                            """
                            UPDATE tb_article 
                            SET title = %s, source = %s, date = %s, 
                                img1 = %s, img2 = %s, n_group = %s, authors = %s, konten = %s, type = %s
                            WHERE link = %s
                        """,
                            (
                                article["title"],
                                article["source"],
                                article["published_date"],
                                article["img1"],
                                article["img2"],
                                article["group"],
                                str(article["authors"]),
                                article["content"],
                                article["type"],
                                article["link"],
                            ),
                        )
                    else:
                        cur.execute(
                            """
                            INSERT INTO tb_article 
                            (link, title, source, date, img1, img2, konten, sentiment, n_group, authors, type)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                            (
                                article["link"],
                                article["title"],
                                article["source"],
                                article["published_date"],
                                article["img1"],
                                article["img2"],
                                article["content"],
                                article["sentiment"],
                                article["group"],
                                str(article["authors"]),
                                article["type"],
                            ),
                        )

                mysql.connection.commit()

            except Exception as e:
                self.logger.error(f"Database error: {e}")
                mysql.connection.rollback()
            finally:
                cur.close()

    def scrape_news(self, group_names, start_date, end_date):
        self.logger.info(f"Starting parallel news scraping for groups: {group_names}")
        cache_key = f"{group_names}_{start_date}_{end_date}"
        if cache_key in self.cache:
            self.logger.info(f"Using cached data for: {cache_key}")
            return self.cache[cache_key]

        # Proceed with scraping
        self.logger.info(
            f"Scraping news for groups: {group_names} within {start_date} - {end_date}"
        )
        all_articles = []
        batch = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_group = {}

            for group in group_names:
                query = requests.utils.quote(group)
                url = f"{self.base_url}?q={query}&hl=id&gl=ID&ceid=ID%3Aid"

                try:
                    response_text = self.fetch_with_cache(url)
                    if not response_text:
                        continue

                    soup = BeautifulSoup(response_text, "html.parser")
                    articles = soup.find_all("article")

                    for article in articles:
                        future = executor.submit(
                            self.process_article, article, group, start_date, end_date
                        )
                        future_to_group[future] = group

                except Exception as e:
                    self.logger.error(f"Error fetching group {group}: {e}")
                    continue

            for future in as_completed(future_to_group):
                try:
                    article_data = future.result()
                    if article_data:
                        batch.append(article_data)
                        all_articles.append(article_data)

                        if len(batch) >= self.batch_size:
                            self.save_articles_batch(batch)
                            batch = []

                except Exception as e:
                    self.logger.error(f"Error processing future: {e}")

            # Save any remaining articles
            if batch:
                self.save_articles_batch(batch)

        self.logger.info(f"Completed scraping with {len(all_articles)} articles")
        self.cache[cache_key] = all_articles
        return all_articles


# Instantiate scraper with desired number of workers
news_scraper = GoogleNewsScraper(max_workers=5, batch_size=50)
