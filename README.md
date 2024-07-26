# qasystem_rag_prompt
## 虚拟环境的配置：
### 创建虚拟环境
 ```sh
   python -m venv qaenv  
   ```
### 启动虚拟环境
 ```sh
   .\qaenv\Scripts\activate
   ```
### 安装依赖
```sh
pip install -r requirements.txt
```
## Install Weaviate by Docker：
### Download your Docker Compose file
```sh
curl -o docker-compose.yml "https://configuration.weaviate.io/v2/docker-compose/docker-compose.yml?generative_anthropic=false&generative_anyscale=false&generative_aws=false&generative_cohere=false&generative_mistral=false&generative_octoai=false&generative_ollama=false&generative_openai=true&generative_openai_key_approval=no&generative_palm=false&gpu_support=false&huggingface_key_approval=no&media_type=text&modules=modules&ner_module=false&qna_module=true&qna_module_model=deepset-roberta-base-squad2&ref2vec_centroid=false&reranker_cohere=false&reranker_transformers=false&runtime=docker-compose&spellcheck_module=false&sum_module=false&text_module=text2vec-huggingface&weaviate_version=v1.26.0&weaviate_volume=named-volume"
```

### set up docker:
```sh
docker-compose up -d
```
### check status：
```sh
docker ps -a
```