from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Initialize the Gemini model (Google GenAI)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    max_tokens=None,
    temperature=0,
    timeout=None,
    max_retries=2,
   
)