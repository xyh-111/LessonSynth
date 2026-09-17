import json
import re
from typing import Type, Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from app.utils.llm import get_llm


def _clean_json_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def invoke_structured_llm(
    system_prompt: str,
    human_prompt: str,
    output_model: Type[BaseModel],
    **kwargs: Any,
) -> BaseModel:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt),
    ])
    chain = prompt | llm
    response = chain.invoke(kwargs)
    json_str = _clean_json_text(response.content)
    data = json.loads(json_str)
    return output_model.model_validate(data)
