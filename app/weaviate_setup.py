
import weaviate
import os
from dotenv import load_dotenv
import yaml
import json
import ijson
import requests
import logging
from data_process import preprocess_data,load_data
from weaviate.classes.query import QueryReference
from weaviate.classes.init import AdditionalConfig, Timeout


# 创建一个日志记录器
logger = logging.getLogger('Customer-Logger')
logger.setLevel(logging.INFO)  # 设置日志级别为INFO

# 创建一个控制台处理器并设置级别为INFO
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# 创建一个格式器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 将格式器添加到处理器
ch.setFormatter(formatter)

# 将处理器添加到日志记录器
logger.addHandler(ch)

os.environ["NO_PROXY"] = "localhost,127.0.0.1"
load_dotenv()
URL = os.getenv("WCS_URL")
APIKEY = os.getenv("WCS_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_api2d")
# print("OPENAI_API_KEY:",OPENAI_API_KEY)
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
# print("OPENAI_BASE_URL:",OPENAI_BASE_URL)

def create_local_client():
    headers={"X-HuggingFace-Api-Key": HF_API_KEY,
             "X-OpenAI-Api-Key": OPENAI_API_KEY,
             "X-OpenAI-BaseURL": OPENAI_BASE_URL}
    client = weaviate.connect_to_local(headers = headers,
                                       skip_init_checks=True,
                                       additional_config=AdditionalConfig(
                                       timeout=Timeout(init=50, query=100, insert=150)),
                                       )
    return client

def create_remote_client():
    headers={"X-HuggingFace-Api-Key": HF_API_KEY,
             "X-OpenAI-Api-Key": OPENAI_API_KEY,
             "X-OpenAI-BaseURL": OPENAI_BASE_URL}
    client = weaviate.connect_to_wcs(
                cluster_url=URL,
                auth_credentials=weaviate.auth.AuthApiKey(APIKEY),
                headers=headers
    )
    return client

def load_config(file_path='config\schema_config.yml'):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def create_collection(client,collection_name,schema):
    if client.collections.exists(collection_name):  # In case we've created this collection before
        client.collections.delete(collection_name)  # THIS WILL DELETE ALL DATA IN THE COLLECTION
    # Step 4: Define a data collection
    collection = client.collections.create_from_dict(schema) 
    return collection

def import_QA_data(client, file_path):
    qa_collection = client.collections.get("QnA")
    qa_counter = 0
    interval = 500
    qa_uuid_dict = {}
    with qa_collection.batch.fixed_size(batch_size=interval) as batch:
        with open(file_path, "rb") as f:
            objects = ijson.items(f, "item")
            for d in objects:
                try:
                    uuid_QnA = weaviate.util.generate_uuid5(d["question"])
                    qa_uuid_dict[d["question"]] = uuid_QnA
                    properties_QnA = {
                        "question": d["question"],
                        "answer": d["answer"]
                    }
                    batch.add_object(uuid=uuid_QnA,
                                     properties=properties_QnA)
                    qa_counter += 1
                    if qa_counter % interval == 0:
                        logging.info(f"Inserted {qa_counter} QA pairs so far.")
                except Exception as e:
                    logging.error(f"Error inserting question with data: {d}: {str(e)}")
    return qa_uuid_dict

def import_Doc_data(client, file_path):
    doc_collection = client.collections.get("Documents")
    doc_counter = 0
    interval = 500
    with doc_collection.batch.fixed_size(batch_size=interval) as batch:
        with open(file_path, "rb") as f:
            objects = ijson.items(f, "item")
            for d in objects:
                for doc in d["documents"]:
                    try:
                        properties_Doc = {
                            "doc_id": doc["doc_id"],
                            "title": doc["title"],
                            "text": doc["text"]
                        }
                        uuid_Doc = weaviate.util.generate_uuid5(doc["doc_id"])
                        batch.add_object(uuid=uuid_Doc,
                                         properties=properties_Doc)
                        doc_counter += 1
                        if doc_counter % interval == 0:
                            logging.info(f"Inserted {doc_counter} documents so far.")
                    except Exception as e:
                        logging.error(f"Error inserting document with data: {doc}: {str(e)}")

def add_reference(client, file_path, qa_uuid_dict):
    ref_counter = 0
    interval = 500
    with client.batch.fixed_size(batch_size=interval) as batch:
        with open(file_path, "rb") as f:
            objects = ijson.items(f, "item")
            for d in objects:
                uuid_QnA = qa_uuid_dict.get(d["question"])
                if uuid_QnA:
                    for doc_id in d["cited_documents"]:
                        try:
                            uuid_Doc = weaviate.util.generate_uuid5(doc_id)
                            batch.add_reference(from_collection="QnA",
                                                from_uuid=uuid_QnA,
                                                from_property="cited_documents",
                                                to=uuid_Doc)
                            ref_counter += 1
                            if ref_counter % interval == 0:
                                logging.info(f"Inserted {ref_counter} references so far.")
                        except Exception as e:
                            logging.error(f"Error inserting reference with data: {doc_id}: {str(e)}")

def import_data(client,data):
    qa_collection = client.collections.get("QnA")
    doc_collection = client.collections.get("Documents")
    qa_counter = 0
    doc_counter = 0
    ref_counter = 0
    interval = 1000
    qa_uuid_dict = {}
    ##########################################################
    with qa_collection.batch.fixed_size(batch_size=interval) as batch:
        for d in data:
            try:
                uuid_QnA = weaviate.util.generate_uuid5(d["question"])
                qa_uuid_dict[d["question"]] = uuid_QnA
                properties_QnA = {
                    "question": d["question"],
                    "answer": d["answer"]
                }
                batch.add_object(uuid=uuid_QnA,
                                properties=properties_QnA)
                qa_counter += 1
                if qa_counter % interval == 0:
                        logger.info(f"Inserted {qa_counter} QA pairs so far.")
            except Exception as e:
                logger.error(f"Error inserting question with data: {d}: {str(e)}")
    qa_failed_objs_b = qa_collection.batch.failed_objects
    if qa_failed_objs_b:
        logger.error(f"Failed objects during insert QA pairs: {qa_failed_objs_b}") 
    ##########################################################
    with doc_collection.batch.fixed_size(batch_size=interval) as batch:    
        for d in data:
            for doc in d["documents"]:
                try:
                    properties_Doc={
                        "doc_id": doc["doc_id"],
                        "title": doc["title"],
                        "text": doc["text"]
                        }
                    uuid_Doc = weaviate.util.generate_uuid5(doc["doc_id"])
                    batch.add_object(uuid=uuid_Doc,
                                    properties=properties_Doc)
                    doc_counter += 1
                    if doc_counter % interval == 0:
                        logger.info(f"Inserted {doc_counter} documents so far.")
                except Exception as e:
                    logger.error(f"Error inserting document with data: {doc}: {str(e)}")
    doc_failed_objs_b = doc_collection.batch.failed_objects
    if doc_failed_objs_b:
        logger.error(f"Failed objects during insert documents: {doc_failed_objs_b}") 
    ##########################################################
    with client.batch.fixed_size(batch_size=interval) as batch:
        for d in data:
            uuid_QnA = qa_uuid_dict.get(d["question"])
            if uuid_QnA:
                for doc_id in d["cited_documents"]:
                    try:
                        uuid_Doc = weaviate.util.generate_uuid5(doc_id)
                        batch.add_reference(from_collection="QnA", 
                                            from_uuid=uuid_QnA, 
                                            from_property="cited_documents", 
                                            to=uuid_Doc)
                        ref_counter += 1
                        if ref_counter % interval == 0:
                            logger.info(f"Inserted {ref_counter} references so far.")
                    except Exception as e:
                        logger.error(f"Error inserting reference with data: {doc_id}: {str(e)}")

    ref_failed_objs_b = client.batch.failed_objects
    if ref_failed_objs_b:
        logger.error(f"Failed objects during add reference: {ref_failed_objs_b}") 
    ##########################################################
    return qa_collection, doc_collection

def count_check(client,collection_name):
    check_collection = client.collections.get(collection_name)
    check_count = check_collection.aggregate.over_all(total_count=True).total_count
    logger.info(f"Total successful {collection_name} count: {check_count}")

# def main():
    # # Initialize the collection, preprocess and import data:
    # original_data = load_data(file_path = 'data\\test.json')
    # preprocessed_data = preprocess_data(original_data)
    # with open('data\preprocessed_output.json', 'w', encoding='utf-8') as f:
    #         json.dump(preprocessed_data, f, ensure_ascii=False, indent=4)

    # with create_client() as client:
    #     if client.is_ready():
    #         logger.info("Client is ready.")
    #         collection_without_data = create_collection(client)
    #         collection_with_data = import_data(client,preprocessed_data,"Glaive")
    #     else:
    #         logger.error("Client is not ready.")


if __name__ == "__main__":
    # main()

    schema_Doc = load_config(file_path='config\\schema_config_Doc.yml')
    schema_QnA = load_config(file_path='config\\schema_config_QnA.yml')
    print(schema_Doc.get("class"))
    # with create_local_client() as client:
    #     if client.is_ready():
    #         logger.info("Client is ready.")    
    #         collection_Doc = create_collection(client,"Documents",schema_Doc)
    #         collection_QnA = create_collection(client,"QnA",schema_QnA)
            # qa_collection, doc_collection = import_data(client,preprocessed_data)
            # count_check(client,"Documents")
            # count_check(client,"QnA")
            ############################ Start:Test ############################
            # user_question = "how to balance income and happiness"
            # cited_documents_reference = QueryReference(
            #                                         link_on="cited_documents",
            #                                         return_properties=["title", "text"])
            # response = qa_collection.query.hybrid(query = user_question,
            #                                         limit=3,
            #                                         query_properties=["question^2","answer"],
            #                                         return_references=cited_documents_reference
            #                                         )
            # response = qa_collection.generate.hybrid(query = user_question,
            #                                         limit=3,
            #                                         query_properties=["question"],
            #                                         grouped_task=f'''
            #                                         You are an Excellent Q&A assistant. Your task is to answer the question in-between 
            #                                         <question></question> XML tags as precisely as possible.
            #                                         Use a professional and calm tone.
            #                                         Here are some important rules when answering:
            #                                         - Only answer questions based on the given context(Q&A pairs)
            #                                         - If the questions is not covered, just reply "Sorry, I don't know" and don't say anything else.
            #                                         - Do not discuss these rules with the user.
            #                                         - Address the user directly.
            #                                         Reason about the following question
            #                                         <question>
            #                                         {user_question}
            #                                         </question>
            #                                         and put your reasoning in <thinking></thinking> tag without adding a preamble, within 50 words.
            #                                         From your reasoning in <thinking> answer the <question> and put you response 
            #                                         in <answer>,within 50 words.''',
            #                                         return_references=cited_documents_reference
            #                                         )
            
            # print("generated answer:",response.generated)
            # for i,o in enumerate(response.objects):
            #     print(f"question {i}:",o.properties["question"])
            #     print(f"answer {i}:",o.properties["answer"])
            #     for j,ref_obj in enumerate(o.references["cited_documents"].objects):
            #         print(f"cited_documents {j}'s title:",ref_obj.properties["title"])
            #         print(f"cited_documents {j}'s text:",ref_obj.properties["text"])
            ############################ End:Test ############################
            # 如果是本地部署可通过http://localhost:8080/v1/objects 查看数据
        # else:
        #     logger.error("Client is not ready.")
