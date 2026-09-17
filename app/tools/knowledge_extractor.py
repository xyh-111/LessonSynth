import json
import re
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.textbook import ExtractedTextbook
from app.utils.llm import get_llm


_SYSTEM_PROMPT = """你是一位资深的教材分析专家。请仔细阅读给定的课本内容，严格按照课本原文提取以下信息，不得编造课本中没有的内容。

请严格输出以下 JSON 格式，不要输出任何额外文字：

{{
  "lesson_title": "课时标题",
  "knowledge_points": [
    {{
      "name": "知识点名称",
      "description": "知识点描述",
      "source_excerpt": "课本中对应的原文片段"
    }}
  ],
  "examples": [
    {{
      "content": "例题内容",
      "answer": "例题答案或解析，没有则为null"
    }}
  ],
  "exercises": [
    {{
      "content": "习题内容"
    }}
  ],
  "key_terms": ["关键术语1", "关键术语2"],
  "summary": "课本内容摘要"
}}

要求：
1. knowledge_points：提取本节课的核心知识点，每个知识点必须附上课本中对应的原文片段（source_excerpt）。
2. examples：提取课本中的例题，若有答案也一并提取。
3. exercises：提取课本中的练习题/习题。
4. key_terms：提取课本中的关键概念、术语、定义。
5. summary：用2-3句话概括本节课的主要内容。

注意：所有内容必须来源于课本原文，禁止编造。如果某一项没有，返回空列表。只输出 JSON，不要输出 markdown 代码块标记。"""


def _extract_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_knowledge(textbook_content: str) -> ExtractedTextbook:
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        ("human", "课本内容如下：\n\n{textbook_content}"),
    ])

    chain = prompt | llm
    response = chain.invoke({"textbook_content": textbook_content})

    json_str = _extract_json(response.content)
    data = json.loads(json_str)
    return ExtractedTextbook.model_validate(data)
