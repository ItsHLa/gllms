import asyncio

from langgraph.checkpoint.memory import InMemorySaver

from src.agent import Agent
from src.llm import LLMFactory
from src.prompt import SYSTEM_PROMPT
from src.vector_store import RAGVectorStore


async def main() -> None:
    model = LLMFactory.create(
        provider="genai",
        model="gemini-3.1-flash-lite-preview",
        temperature=0,
    )

    checkpointer = InMemorySaver()
    vectorstore = RAGVectorStore()
    tool = vectorstore.get_retriever_tool()

    agent = Agent(
        model=model,
        checkpointer=checkpointer,
        system_prompt=SYSTEM_PROMPT,
        tools=[tool],
    )

    text = agent.call(
        user_prompt="hello, what are the main policy of the company? What data u collect?",
        session_id="1",
    )
    print(text)


if __name__ == "__main__":
    asyncio.run(main())

