from transformers import AutoModel, AutoTokenizer
import torch
# 0724:之前docker使用了默认的配置，缺少相应的module，重新配置后应该不需要这个手动embedding的函数了
# 要开启developer mode，否则报无法符号链接的warning
# 可以通过transformers-cli cache --cleanup --model <model_name>清理缓存！
# 尝试stella_en_400M_v5模型和分词器 -> 不行，强制依赖xformers，没有gpu
# 尝试jamesgpt1/sf_model_e5 -> 可以，不用cuda
# 尝试mixedbread-ai/mxbai-embed-large-v1 -> 可以
# 尝试 Alibaba-NLP/gte-large-en-v1.5 -> 要远程
# 首次加载某个预训练模型时，Hugging Face 的 transformers 库会从 Hugging Face Hub 下载模型文件（例如权重、配置文件等）到本地缓存。
tokenizer = AutoTokenizer.from_pretrained('Alibaba-NLP/gte-large-en-v1.5', trust_remote_code=True)
embedding_model = AutoModel.from_pretrained('Alibaba-NLP/gte-large-en-v1.5', trust_remote_code=True)


def get_embedding(text):
    """
    获取给定文本的嵌入向量。
    
    Args:
    - text (str): 输入文本。
    
    Returns:
    - List[float]: 文本的嵌入向量。
    """
    # 使用分词器对文本进行编码
    inputs = tokenizer(text, return_tensors="pt")
    
    # 使用模型获取文本的嵌入表示
    with torch.no_grad():
        # 不需要计算梯度，因为我们不进行模型参数的更新。
        outputs = embedding_model(**inputs)
    print(outputs.last_hidden_state.shape)
    print(outputs.last_hidden_state.mean(dim=1).shape)
    print(outputs.last_hidden_state.mean(dim=1).squeeze().shape)
    # 取最后一层隐藏状态的平均值(是一种常见做法）作为文本的嵌入向量
    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
    # outputs.last_hidden_state：获取最后一层的隐藏状态（每个单词或子词对应一个向量）。
    # .mean(dim=1)：计算每个句子的所有单词或子词向量的平均值，得到整个句子的嵌入表示。
    # .squeeze()：去除不必要的维度。
    # .tolist()：将PyTorch张量转换为Python列表，便于后续处理。
    
    return embeddings

if __name__ == "__main__":
    test = get_embedding(text = "Hello,world!")
    print(len(test))