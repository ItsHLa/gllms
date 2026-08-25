class LLMFactory:

    @staticmethod
    def create(model: str, provider: str, temperature: float):
        if provider == "genai":
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(model=model, temperature=temperature)
        raise ValueError(f"Unsupported provider: {provider}")