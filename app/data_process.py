import json
import re
def load_data(file_path = 'data\\glaive_rag_v1.json'):
    """
    从JSON文件加载数据。
    
    Args:
    - file_path (str): JSON数据文件的路径。
    
    Returns:
    - List[dict]: 数据项的列表。
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# def extract_cited_documents(answer):
#     """
#     从答案中提取引用的文档ID。
    
#     Args:
#     - answer (str): 答案文本。
    
#     Returns:
#     - List[str]: 引用的文档ID列表。
#     """
#     cited_docs = re.findall(r"<co:(\d+)>", answer)
#     return list(set(cited_docs))

# def preprocess_data(data):
#     """
#     ***用split+if/else实现,但无法覆盖所有pattern。

#     对数据进行预处理，如清理文本、分割文档和规范字段。
    
#     Args:
#     - data (List[dict]): 数据项的列表。
    
#     Returns:
#     - List[dict]: 预处理后的数据项列表。
#     """
#     preprocessed_data = []

#     for idx, item in enumerate(data):
#         try:
#             system_prompt = item["system_prompt"].strip().replace('\n', '')
#             documents = item["documents"].strip().replace('\n', '')
#             documents = documents[9:]
#             documents = documents.split("Document:")
#             documents = ["Document ID:" + doc.strip() for doc in documents]
#             # print("*****"*10)
#             # print("documents:",documents)
#             preprocessed_documents = []
#             for doc in documents:
#                 # try:
#                 # print("---"*10)
#                 # print("doc:",doc)
#                 doc_parts = doc.split("Title:")
#                 # print("doc_parts:",doc_parts)                   
#                 doc_id = doc_parts[0].replace("Document ID:", "").strip()
#                 if len(doc_parts) > 1:
#                     doc_title = doc_parts[1].split("Text:")[0].strip()
#                     if len(doc_parts[1].split("Text:"))>1:
#                         doc_text = doc_parts[1].split("Text:")[1].strip()
#                     else:
#                         doc_text = ""
#                 else:
#                     doc_title = ""
#                     doc_text = ""
#                 preprocessed_documents.append({
#                     "doc_id": doc_id,
#                     "title": doc_title,
#                     "text": doc_text
#                 })
#                     # except IndexError as e:
#                     #     print(f"Error processing item with length: {len(doc_parts)} at: {doc}")
#                     #     raise e
                        
                
#             question = item["question"].strip().replace('\n', '')
#             answer_mode = item["answer_mode"].strip().replace('\n', '')
#             if "Answer:" in item["answer"]:
#                 answer = item["answer"].split("Answer:")[1].strip().replace('\n', '')
#             else:
#                answer = item["answer"].strip().replace('\n', '')
#             cited_docs = extract_cited_documents(answer)

#             preprocessed_data.append({
#                 "system_prompt": system_prompt,
#                 "documents": preprocessed_documents,
#                 "question": question,
#                 "answer_mode": answer_mode,
#                 "answer": answer,
#                 "cited_documents": cited_docs
#             })

#         except IndexError as e:
#             print(f"Error processing item at index {idx}: {item}")
#             raise e


#     return preprocessed_data

def preprocess_data(data):
    """
    ***尝试用正则表达式进行预处理
    ***对于不合规范的数据（例如document只有title却没有text,还有没有answer的)，直接跳过

    对数据进行预处理，如清理文本、分割文档和规范字段。
    
    Args:
    - data (List[dict]): 数据项的列表。
    
    Returns:
    - List[dict]: 预处理后的数据项列表。
    """
    preprocessed_data = []

    # Document:(\d+)：匹配 "Document:" 后的一个或多个数字，group 1。
    # \s*：匹配零个或多个空白字符。
    # Title:(.*?)：匹配 "Title:" 后的任意字符（非贪婪），group 2。
    # \s*：匹配零个或多个空白字符。
    # Text:(.*?)：匹配 "Text:" 后的任意字符（非贪婪），group 3。
    # \s*：匹配零个或多个空白字符。
    # (?=Document:|$)：正向先行断言，匹配下一个 "Document:" 或字符串结尾。
    document_pattern = re.compile(r'Document:(\d+)\s*Title:(.*?)\s*Text:(.*?)\s*(?=Document:|$)', re.DOTALL)
    # Cited Documents:\s*([\d, ]+)：匹配 "Cited Documents:" 后的一个或多个数字和逗号，group 1。
    # \s*：匹配零个或多个空白字符。
    # Answer:\s*(.*)：匹配 "Answer:" 后的任意字符（包括换行符），group 2。
    answer_pattern = re.compile(r'Cited Documents:\s*([\d, ]+|None)\s*Answer:\s*(.*)', re.DOTALL)
    # <co:(\d+)>：匹配 <co:> 标签中包含的一个或多个数字，group 1。
    cited_docs_pattern = re.compile(r'<co:(\d+)>')

    for idx, item in enumerate(data):
        try:
            system_prompt = item["system_prompt"].strip().replace('\n', '')
            documents = item["documents"].strip().replace('\n', '')
            preprocessed_documents = []

            for match in document_pattern.finditer(documents):
                # 给doc_id加上index，防止重复
                doc_id = f"{idx}-{match.group(1).strip()}"  # Prefix doc_id with an index to make it unique
                doc_title = match.group(2).strip()
                doc_text = match.group(3).strip()
                preprocessed_documents.append({
                    "doc_id": doc_id,
                    "title": doc_title,
                    "text": doc_text
                })
            
            question_id = idx
            question = item["question"].strip().replace('\n', '')
            answer_mode = item["answer_mode"].strip().replace('\n', '')

            answer_match = answer_pattern.search(item["answer"])
            if answer_match:
                cited_docs_str = answer_match.group(1).strip()
                answer = answer_match.group(2).strip().replace('\n', '')
                if cited_docs_str.lower() == 'none':
                    cited_docs = []
                else:
                    cited_docs = [f"{idx}-{doc_id.strip()}" for doc_id in cited_docs_str.split(',')]
            else:
                answer = ''
                cited_docs = []

            preprocessed_data.append({
                "question_id": question_id,
                "question": question,
                "answer": answer,
                "cited_documents": cited_docs,
                "documents": preprocessed_documents
            })

        except (IndexError, AttributeError) as e:
            print(f"Error processing item at index {idx}: {item}")
            raise e

    return preprocessed_data

def write_preprocessed_data(preprocessed_data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(preprocessed_data, f, ensure_ascii=False, indent=4)

def main_preprocess_data():
    input_path = 'data\glaive_rag_v1.json'
    output_path = 'data\preprocessed_output.json'
    data = load_data(file_path = input_path)
    preprocessed_data = preprocess_data(data)
    write_preprocessed_data(preprocessed_data, output_path)
    print("Preprocessed data saved to:", output_path)

if __name__ == "__main__":
    main_preprocess_data()
