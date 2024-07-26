import weaviate
import os
import yaml
from dotenv import load_dotenv
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

load_dotenv()

URL = os.getenv("WCS_URL")
APIKEY = os.getenv("WCS_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_api2d")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

with weaviate.connect_to_local(
    headers={"X-HuggingFace-Api-Key": HF_API_KEY,
             "X-OpenAI-Api-Key": OPENAI_API_KEY,
             "X-OpenAI-BaseURL": OPENAI_BASE_URL}) as client:
    print("if client is ready:",client.is_ready())
    meta_info = client.get_meta()
    print("meta_info:"meta_info)

