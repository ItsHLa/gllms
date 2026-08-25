from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()


class Agent:
    def __init__(
        self,
        model,
        checkpointer,
        system_prompt: str = "You are a helpful assistant",
        tools: list | None = None,
    ):
        self.agent = create_agent(
            model=model,
            tools=tools or [],
            checkpointer=checkpointer,
            system_prompt=system_prompt,
        )

    def get_config(self, session_id: str) -> dict:
        return {"configurable": {"thread_id": session_id}}

    def call(self, user_prompt: str, session_id: str):
        return self.call_with_trace(user_prompt, session_id)["response"]

    def call_with_trace(self, user_prompt: str, session_id: str) -> dict:
        config = self.get_config(session_id)
        response = self.agent.invoke(
            {"messages": {"role": "user", "content": user_prompt}},
            config=config,
        )

        messages = response["messages"]
        tool_calls = []
        for msg in messages:
            for call in getattr(msg, "tool_calls", []) or []:
                tool_calls.append({"name": call.get("name"), "args": call.get("args")})

        return {
            "response": messages[-1].content,
            "messages": messages,
            "tool_calls": tool_calls,
        }