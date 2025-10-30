from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import os

load_dotenv()

firecrawl_app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))