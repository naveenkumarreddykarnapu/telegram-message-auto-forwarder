import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

# Configuration
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')

client = TelegramClient('userbot_session', api_id, api_hash)

# Function to log in and retrieve account info
async def main():
    # Start the client and log in
    await client.start()

    # Fetch account details
    me = await client.get_me()
    
    # Display the phone number and other account information
    print(f"Phone number: {me.phone}")
    print(f"Username: {me.username}")
    print(f"First name: {me.first_name}")
    print(f"Last name: {me.last_name}")
    print(f"User ID: {me.id}")

# Run the client and retrieve the info
with client:
    client.loop.run_until_complete(main())
