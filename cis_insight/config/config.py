import dotenv
import os

dotenv.load_dotenv()

DB_DIR = os.getenv("DB_DIR")
DB_NAME = os.getenv("DB_NAME")
DB_PATH = os.path.join(DB_DIR, DB_NAME)
