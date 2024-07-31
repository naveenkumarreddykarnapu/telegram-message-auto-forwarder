from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel, PeerChat, PeerUser
import sqlite3
import requests
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta, timezone
import re
import logging
import tweepy
import os

# Configuration
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
source_channels = [-1001562954261, -1001363680849, -1001315464303, -1001707571730]
destination_chat = os.getenv('TARGET')
twitter_channel = int(os.getenv('TWITTER_CHANNEL'))
error_notify = os.getenv('ERROR_NOTIFY')

# Twitter API credentials
twitter_creds = {
    'consumer_key': os.getenv('TWITTER_CONSUMER_KEY'),
    'consumer_secret': os.getenv('TWITTER_CONSUMER_SECRET'),
    'access_token': os.getenv('TWITTER_ACCESS_TOKEN'),
    'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
}

# Initialize the Telegram client
client = TelegramClient('userbot_session', api_id, api_hash)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register adapters and converters to handle datetime objects with SQLite
def init_db():
    sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
    sqlite3.register_converter("DATETIME", lambda dt_str: datetime.fromisoformat(dt_str.decode('utf-8')))
    conn = sqlite3.connect('processed_messages.db', detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                      message_id INTEGER PRIMARY KEY, 
                      message_text TEXT, 
                      url_endpoint TEXT, 
                      channel_id TEXT,
                      timestamp DATETIME)''')
    return conn, cursor

conn, cursor = init_db()

def extract_product_id(url):
    try:
        response = requests.get(url, allow_redirects=True, timeout=10)
        final_url = response.url
        parsed_url = urlparse(final_url)
        path_segments = parsed_url.path.split('/')
        query_params = parse_qs(parsed_url.query)
        
        # Check for product ID in different e-commerce sites
        if 'amazon' in parsed_url.netloc:
            for segment in path_segments:
                if re.match(r'^B[A-Z0-9]{9}$', segment):
                    return segment
        elif 'flipkart' in parsed_url.netloc:
            pid = query_params.get('pid', [''])[0]
            if pid:
                return pid
        # Generic check for any site URL containing an ID
        for key, values in query_params.items():
            if 'id' in key:
                return values[0]
        for segment in path_segments:
            if re.match(r'^[A-Za-z0-9]{10,}$', segment):
                return segment
        for key, values in query_params.items():
            for value in values:
                if re.match(r'^[A-Za-z0-9]{10,}$', value):
                    return value
        return parsed_url.netloc + parsed_url.path + '?' + parsed_url.query
    except requests.RequestException as e:
        logger.error(f"Error resolving URL {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None

def is_duplicate_message(new_product_id, time_limit):
    cursor.execute("SELECT * FROM messages WHERE url_endpoint = ? AND timestamp >= ?", 
                   (new_product_id, time_limit))
    return cursor.fetchone() is not None

def extract_urls(message_text):
    return re.findall(r'(https?://\S+)', message_text)

def post_to_twitter(message_text):
    try:
        cleaned_message = re.sub(r'\b[Ll]+[Oo]+[Oo]+[Tt]+\b', '', message_text, flags=re.IGNORECASE).strip()
        client = tweepy.Client(consumer_key=twitter_creds['consumer_key'], 
                               consumer_secret=twitter_creds['consumer_secret'],
                               access_token=twitter_creds['access_token'], 
                               access_token_secret=twitter_creds['access_token_secret'])
        response = client.create_tweet(text=cleaned_message)
        if response.errors:
            logger.error(f"Error posting to Twitter: {response.errors}")
    except Exception as e:
        logger.error(f"Error posting to Twitter: {e}")

@client.on(events.NewMessage(chats=source_channels))
async def handler(event):
    try:
        message_id = event.message.id
        message_text = event.message.message
        peer_id = event.message.peer_id
        channel_id = (peer_id.channel_id if isinstance(peer_id, PeerChannel) else
                      peer_id.chat_id if isinstance(peer_id, PeerChat) else
                      peer_id.user_id if isinstance(peer_id, PeerUser) else None)
        
        if not channel_id:
            logger.warning("Unknown peer type")
            return
        
        if channel_id == twitter_channel:
            post_to_twitter(message_text)
            return

        urls = extract_urls(message_text)
        if not urls:
            return

        product_id = extract_product_id(urls[0])
        if not product_id or is_duplicate_message(product_id, datetime.now(timezone.utc) - timedelta(hours=6)):
            return

        await client.send_message(destination_chat, event.message)
        
        cursor.execute("INSERT INTO messages (message_id, message_text, url_endpoint, channel_id, timestamp) VALUES (?, ?, ?, ?, ?)",
                       (message_id, message_text, product_id, channel_id, datetime.now(timezone.utc)))
        conn.commit()
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await client.send_message(error_notify, f"Error: {e}")

async def main():
    await client.start()
    logger.info("Userbot started!")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
