from langchain_openai import ChatOpenAI
from app.config import settings


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        temperature=0.3,
    )


def get_vision_llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_vision_model,
        temperature=0.1,
    )
