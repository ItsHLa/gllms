class LLMFactory:

    @staticmethod
    def create(model, provider, temperature):
        if provider == 'genai':
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model = model,
                temperature = temperature
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")