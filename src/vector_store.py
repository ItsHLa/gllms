import os
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
from src.embeddings import EmbeddingsFactory
from langchain_core.tools import create_retriever_tool

load_dotenv()

class RAGVectorStore:

    def __init__(
        self,
        index_name = 'generativellmsecurity',
        embeddings = 'sentence-transformers/distilbert-base-nli-mean-tokens'):
        self.API_KEY = os.getenv("PINECONE_API_KEY")  
        self.embeddings = EmbeddingsFactory.create(model = embeddings) 
        self.vectorstore = PineconeVectorStore(index_name = index_name, embedding = self.embeddings)    
    
    def retriever(self, query):
        retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwags = { "k" : 3, "score_threshold" : 0.4}
        )
        result = retriever.invoke(query)
        return result
    
    def get_retriever_tool(self):
        retriever = self.vectorstore.as_retriever(search_kwags = { "k" : 3, "score_threshold" : 0.4})
        return create_retriever_tool(retriever, name = "knowledgebase", description = "Use this tool to retrieve answers about company privacy and policy")