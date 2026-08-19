from dotenv import load_dotenv
import os
from langchain_huggingface import HuggingFaceEndpointEmbeddings
load_dotenv()

class EmbeddingsFactory:
    
    @staticmethod
    def create(model):
        return HuggingFaceEndpointEmbeddings(
            model = model,
            task="feature-extraction",
            huggingfacehub_api_token=os.getenv("HUGGINGFACE_API_KEY")
        )

