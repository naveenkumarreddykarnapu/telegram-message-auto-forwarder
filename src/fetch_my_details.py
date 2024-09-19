import os
from dotenv import load_dotenv
from telethon import TelegramClient

# Load environment variables from .env file
load_dotenv()

# Configuration
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')

# Create a new TelegramClient session
client = TelegramClient('userbot_session', api_id, api_hash)

# Function to log in and retrieve messages from the Telegram bot
async def print_verification_messages():
    # Start the client and log in
    await client.start()

    # Get a list of your dialogs (chats and messages)
    async for dialog in client.iter_dialogs():
        # Check if the dialog is with the official Telegram bot (can use bot username or ID)
        if dialog.name == "Telegram" or dialog.entity.bot:  # "Telegram" is typically the bot's display name
            print(f"Found chat with Telegram Bot: {dialog.name}")

            # Fetch and print the last 10 messages from the Telegram bot
            async for message in client.iter_messages(dialog.id, limit=10):
                print(f"Message from Telegram bot: {message.text}")

# Run the client and retrieve the verification messages
with client:
    client.loop.run_until_complete(print_verification_messages())
