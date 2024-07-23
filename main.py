import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout
import os

os.environ["NO_PROXY"] = "localhost,127.0.0.1"

client = weaviate.connect_to_local()

print(client.is_ready())
client.close()