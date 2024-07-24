import weaviate
from app.embedding_model import get_embedding, tokenizer, embedding_model

def retrieve_documents(cited_documents):
    """
    根据引用的文档ID-cited documents从Weaviate检索相关文档。
    
    Args:
    - cited_documents (List[str]): 引用的文档ID列表。
    
    Returns:
    - List[dict]: 检索到的文档列表。
    """
    documents = []
    with weaviate.Client(url=WEAVIATE_URL) as client:
        for doc_id in cited_documents:
            result = client.data_object.get_by_id(doc_id)
            if result:
                documents.append(result['properties']['text'])
    
    return documents

def generate_answer(documents, question):
    """
    使用检索到的文档和输入问题生成答案。
    
    Args:
    - documents (List[str]): 检索到的文档列表。
    - question (str): 输入问题。
    
    Returns:
    - str: 生成的答案。
    """
    context = " ".join(documents)
    input_text = f"{context}\n\nQuestion: {question}\nAnswer:"
    inputs = tokenizer.encode(input_text, return_tensors="pt")
    outputs = embedding_model.generate(inputs, max_length=150)
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return answer