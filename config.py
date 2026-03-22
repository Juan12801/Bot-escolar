from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID") or "-1")
NOTIFICATION_HOUR = int(os.getenv("NOTIFICATION_HOUR") or "15")
