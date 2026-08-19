from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()

class Agent:

    def __init__(
        self,
        model,
        checkpointer,
        system_prompt = 'You are a helpful assistant',
        tools = []
        ):
        self.agent = create_agent(
            model = model,
            tools = tools,
            checkpointer = checkpointer,
            system_prompt = system_prompt
        )
    
    def get_config(self, session_id):
        return {"configurable": {"thread_id": session_id}}

    def call(self, user_prompt, session_id):
        config = self.get_config(session_id)
        response = self.agent.invoke(
            {
                'messages' : {'role' : 'user', 'content': user_prompt}
            },
            config = config)
        return response['messages'][-1].content