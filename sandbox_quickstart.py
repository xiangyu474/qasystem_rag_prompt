import weaviate
import os
from dotenv import load_dotenv
import json
import requests
# load .env 
load_dotenv()

# Set these environment variables
URL = os.getenv("WCS_URL")
APIKEY = os.getenv("WCS_API_KEY")
# embedding model
HF_API_KEY = os.getenv("HF_API_KEY")
# generative model
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_api2d")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
# print("OPENAI_API_KEY:",OPENAI_API_KEY)
# print("OPENAI_BASE_URL:",OPENAI_BASE_URL)

# 定义集合架构
schema = {
    "class": "Question",
    "vectorizer": "text2vec-huggingface",
    "moduleConfig": {
        "text2vec-huggingface": {
            "model": "intfloat/e5-small-v2",
            "options": {"waitForModel": True}
        },
        "generative-openai": {
            "model": "gpt-3.5-turbo",
            "options": {"waitForModel": True}
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
             "X-OpenAI-Api-Key": OPENAI_API_KEY,
             "X-OpenAI-BaseURL": OPENAI_BASE_URL}) as client:

    print("if client is ready:",client.is_ready())

    if client.collections.exists("Question"):  # In case we've created this collection before
        client.collections.delete("Question")  # THIS WILL DELETE ALL DATA IN THE COLLECTION

    # Step 4: Define a data collection
    questions = client.collections.create_from_dict(schema) 
    
    # Step 5: Add objects
    question_objs = list()
    for i, d in enumerate(data):
        question_objs.append({
            "answer": d["Answer"],
            "question": d["Question"],
            "category": d["Category"],
            "index": i
        })
    # questions = client.collections.get("Question")
    questions.data.insert_many(question_objs)
    response = questions.aggregate.over_all(total_count=True)
    # print(response.total_count)
    # print(questions)

#     # Vector (near text) search:
#     response_near_text= questions.query.near_text(
#     query="what is dna?",  # The model provider integration will automatically vectorize the query
#     limit=3
# )

#     for obj in response_near_text.objects:
#         print(obj.properties)

#     # hybrid search:
#     response_hybrid= questions.query.hybrid(
#     query="what is dna?",  # The model provider integration will automatically vectorize the query
#     limit=3
# )
#     for obj in response_hybrid.objects:
#         print(obj.properties)
   
# RAG:generate_hybrid
# instruction for the generative module
    user_question = "what is dna?"
    response = questions.generate.hybrid(
        query=user_question,
        query_properties=["answer"],
        grouped_task=f"Based on the following documents, answer the question: {user_question}",
        limit=2
    )

    print("generated answer:",response.generated)  # "Grouped task" generations are attributes of the entire response
    for o in response.objects:
        print(o.properties['category'])  # To inspect the retrieved object