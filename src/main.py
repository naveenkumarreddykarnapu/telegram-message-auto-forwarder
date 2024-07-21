import os
from telethon import TelegramClient, events, sync

api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
source = os.getenv('SOURCE')
target = os.getenv('TARGET')
error_notify = os.getenv('ERROR_NOTIFY')

client = TelegramClient('userbot_session', api_id, api_hash)

@client.on(events.NewMessage(chats=source))
async def handler(event):
    try:
        await client.send_message(target, event.message)
        print(f"Message forwarded to {target}")
    except Exception as e:
        print(f"Failed to forward message: {e}")
        await client.send_message(error_notify, f"Failed to forward message: {e}")

async def main():
    await client.start()  
    print("Userbot started!")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
