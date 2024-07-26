# 创建链接
# 创建collection - glaive_rag_v1
# 嵌入数据
import weaviate
import os
from dotenv import load_dotenv
import yaml
import json
from data_process import preprocess_data,load_data

os.environ["NO_PROXY"] = "localhost,127.0.0.1"
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_api2d")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

def create_client():
    headers={"X-HuggingFace-Api-Key": HF_API_KEY,
             "X-OpenAI-Api-Key": OPENAI_API_KEY,
             "X-OpenAI-BaseURL": OPENAI_BASE_URL}
    client = weaviate.connect_to_local(headers = headers)
    return client

def load_config(file_path='config\schema_config.yml'):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def create_collection(client):
    # with create_client() as client:
    schema = load_config(file_path='config\schema_config.yml')
    if client.collections.exists("Glaive"):  # In case we've created this collection before
        client.collections.delete("Glaive")  # THIS WILL DELETE ALL DATA IN THE COLLECTION
    # Step 4: Define a data collection
    qa_collection = client.collections.create_from_dict(schema) 

    return qa_collection

def import_data(client,data,collection_name):
    # with create_client() as client:
    # Step 5: Add objects
    qa_collection = client.collections.get(collection_name)
    # qa_data_objs = list()
    # The batch size and the number of concurrent requests are dynamically adjusted on-the-fly during import, depending on the server load.
    with qa_collection.batch.dynamic() as batch:
        for d in data:
            for doc in d["documents"]:
                try:
                    properties={
                        "doc_id": doc["doc_id"],
                        "question": d["question"],
                        "answer": d["answer"],
                        "title": doc["title"],
                        "text": doc["text"]
                        }
                    #  NOTE: If the UUID of one of the objects already exists then the existing object will be replaced by the new object.
                    obj_uuid = weaviate.util.generate_uuid5(properties)
                    print(f"Inserting document with UUID: {obj_uuid}")
                    batch.add_object(uuid=obj_uuid,
                                    properties=properties)
                except Exception as e:
                    print(f"Error inserting document with UUID: {obj_uuid}: {e}")   
                # qa_data_objs.append({
                #     "doc_id": doc["doc_id"],
                #     "question": d["question"],
                #     "answer": d["answer"],
                #     "title": doc["title"],
                #     "text": doc["text"]
                # })

    # qa_collection.data.insert_many(qa_data_objs)

    return qa_collection


if __name__ == "__main__":
    schema = load_config(file_path='config\schema_config.yml')
    original_data = load_data(file_path = 'data\glaive_rag_v1.json')
    preprocessed_data = preprocess_data(original_data)
    with open('data\preprocessed_output.json', 'w', encoding='utf-8') as f:
            json.dump(preprocessed_data, f, ensure_ascii=False, indent=4)
    with create_client() as client:
        print("if client is ready:",client.is_ready())
        collection_without_data = create_collection(client)
        print("collection_without_data:",collection_without_data)
        collection_with_data = import_data(client,preprocessed_data,"Glaive")
        response = collection_with_data.aggregate.over_all(total_count=True)
        print("data count:",response.total_count)
