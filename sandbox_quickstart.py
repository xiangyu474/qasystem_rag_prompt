import weaviate
import os
from dotenv import load_dotenv
import json
import requests
# load .env 
load_dotenv()

# Set these environment variables
URL = os.getenv("WCS_URL")
# print("URL:",URL)
APIKEY = os.getenv("WCS_API_KEY")
# print("APIKEY:",APIKEY)
HF_API_KEY = os.getenv("HF_API_KEY")

# 定义集合架构
schema = {
    "class": "Question",
    "vectorizer": "text2vec-huggingface",
    "moduleConfig": {
        "text2vec-huggingface": {
            "pooling": "mean",
            # 尝试换一个小模型：
            # avsolatorio/NoInstruct-small-Embedding-v0 ->超时
            # sentence-transformers/all-MiniLM-L12-v2还是超时
            "model": "sentence-transformers/all-MiniLM-L12-v2",
            # "model": "Alibaba-NLP/gte-large-en-v1.5",
            # 也许因为模型太大所以一直报503 error:timeout
            "Options":{"wait_for_model":True,
                       "trust_remote_code":True}
            # 这样写根本不生效，来源：https://huggingface.co/docs/api-inference/detailed_parameters，https://discuss.huggingface.co/t/what-is-model-is-currently-loading/13917/12
            # 考虑全部使用手动嵌入，不在插数据的时候用vecotorizer自动嵌入了
        },
        "generative-huggingface": {
            "model": "google/flan-t5-base",
            "Options":{"wait_for_model":True,
                       "trust_remote_code":True}
        }
    }
}

#拉取data
resp = requests.get('https://raw.githubusercontent.com/weaviate-tutorials/quickstart/main/data/jeopardy_tiny.json')
data = json.loads(resp.text) 

with weaviate.connect_to_wcs(
    cluster_url=URL,
    auth_credentials=weaviate.auth.AuthApiKey(APIKEY),
    headers={"X-HuggingFace-Api-Key": HF_API_KEY,
    # 添加 Hugging Face 访问令牌,否则有报错raise WeaviateInsertManyAllFailedError(
    # weaviate.exceptions.WeaviateInsertManyAllFailedError: Every object failed during insertion. Here is the set of all errors: failed with status: 429 error: Rate limit reached. Please log in or use a HF access token
    }) as client:

    print("if client is ready:",client.is_ready())

    client.collections.delete("Question")
    collections = client.collections.list_all()
    collection_exists = "Question" in collections
    print("if collection exists:",collection_exists)
    
    if not collection_exists:
        # Step 4: Define a data collection
        questions = client.collections.create_from_dict(schema)  
    # Step 5: Add objects
    question_objs = list()
    for i, d in enumerate(data):
        question_objs.append({
            "answer": d["Answer"],
            "question": d["Question"],
            "category": d["Category"],
        })

    questions = client.collections.get("Question")
    questions.data.insert_many(question_objs)
    print(questions)