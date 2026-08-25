import os

from dotenv import load_dotenv
from langchain_core.tools import create_retriever_tool
from langchain_pinecone import PineconeVectorStore

from src.embeddings import EmbeddingsFactory

load_dotenv()


class RAGVectorStore:
    def __init__(
        self,
        index_name: str = "generativellmsecurity",
        embeddings: str = "sentence-transformers/distilbert-base-nli-mean-tokens",
    ):
        self.embeddings = EmbeddingsFactory.create(model=embeddings)
        self.vectorstore = PineconeVectorStore(
            index_name=index_name, embedding=self.embeddings
        )

    def retriever(self, query: str):
        retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 3, "score_threshold": 0.4},
        )
        return retriever.invoke(query)

    def get_retriever_tool(self):
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 3, "score_threshold": 0.4}
        )
        return create_retriever_tool(
            retriever,
            name="knowledgebase",
            description="Use this tool to retrieve answers about company privacy and policy",
        )