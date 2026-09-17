# LessonSynth 后端逻辑文档

> 基于 LangGraph 的多智能体教学活动设计系统后端实现说明。

## 1. 项目概览

LessonSynth 是一个教学活动设计 Agent，接收学科、年级、课时标题和课本内容（文本或文件），自动生成一份结构化、可审核修改的完整教案。

核心流程：

```
用户输入 → 课本解析/知识点抽取 → 教学目标 → 重点难点 → 教学过程设计 → 审核 → (不通过则修改) → 输出教案
```

## 2. 目录结构

```
app/
├── main.py                    # FastAPI 应用入口，挂载路由与 CORS
├── config.py                  # 全局配置（DeepSeek API 密钥、模型、端口等）
├── api/
│   ├── __init__.py
│   └── lesson.py              # 教案生成相关 HTTP 接口
├── agents/
│   ├── __init__.py
│   ├── graph.py               # LangGraph 状态图编排（核心流程）
│   ├── state.py               # 全局状态 AgentState 定义
│   ├── llm_helper.py          # 结构化 LLM 调用工具（提示词 + JSON 解析 + Pydantic 校验）
│   ├── textbook_parser_agent.py   # 课本解析 Agent
│   ├── objective_agent.py     # 教学目标 & 重点难点 Agent
│   ├── process_agent.py       # 教学过程设计 Agent
│   └── reviewer_agent.py      # 教案审核 Agent
├── tools/
│   ├── __init__.py
│   ├── textbook_parser.py     # 多格式文件解析（PDF/DOCX/TXT/图片）
│   ├── knowledge_extractor.py # 知识点抽取（LLM 调用）
│   └── image_ocr.py           # 图片 OCR（视觉模型）
├── schemas/
│   ├── input.py               # 用户输入模型
│   ├── textbook.py            # 课本抽取结果模型
│   ├── output.py              # 教案输出模型
│   └── review.py              # 审核结果模型
└── utils/
    └── llm.py                 # LLM 客户端工厂（文本模型 & 视觉模型）
```

## 3. 入口与配置

### 3.1 `app/main.py`

- 使用 **FastAPI** 创建应用，挂载 `lesson_router` 路由。
- 配置 **CORS** 中间件，允许所有来源、方法、头部（开发环境）。
- 提供 `GET /` 服务状态检查、`GET /health` 健康检查接口。

### 3.2 `app/config.py`

基于 `pydantic_settings.BaseSettings`，从 `.env` 文件读取配置：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `deepseek_api_key` | 内置默认 | DeepSeek API 密钥 |
| `deepseek_base_url` | `https://api.deepseek.com/v1` | API 基础地址 |
| `deepseek_model` | `deepseek-v4-pro` | 文本生成模型 |
| `deepseek_vision_model` | `deepseek-chat` | 视觉/OCR 模型 |
| `app_host` | `0.0.0.0` | 服务监听地址 |
| `app_port` | `8000` | 服务端口 |

## 4. HTTP 接口层（`app/api/lesson.py`）

路由前缀：`/api`

### 4.1 `POST /api/parse-file` — 文件解析

- **入参**：`multipart/form-data`，字段 `file`
- **逻辑**：读取上传文件 → `parse_textbook_bytes` 按扩展名分发解析器 → 返回文本内容
- **支持格式**：`.pdf`、`.docx/.doc`、`.txt/.md`、`.png/.jpg/.jpeg/.webp/.bmp/.gif`
- **返回**：`{ filename, content }`

### 4.2 `POST /api/generate` — 生成教案

- **入参**：`TextbookInput`（JSON Body）
- **逻辑**：校验课本内容非空 → `build_graph()` 构建状态图 → `graph.invoke()` 执行完整 Agent 流程 → 组装 `LessonPlanOutput` 返回
- **返回**：`LessonPlanOutput`（结构化教案 JSON）

### 4.3 `GET /api/generate/info` — 流程信息

返回 Agent 流程的各阶段说明及最大修改轮次（`max_revisions = 2`）。

## 5. LLM 工具层

### 5.1 `app/utils/llm.py`

提供两个 LLM 客户端工厂函数，均基于 `langchain_openai.ChatOpenAI`：

- `get_llm()`：文本生成模型（`temperature=0.3`），用于文本生成与结构化抽取。
- `get_vision_llm()`：视觉模型（`temperature=0.1`），用于图片 OCR。

### 5.2 `app/agents/llm_helper.py` — 结构化调用封装

`invoke_structured_llm(system_prompt, human_prompt, output_model, **kwargs)`：

1. 构建 `ChatPromptTemplate`（system + human）。
2. 以 `prompt | llm` 链式调用。
3. 用 `_clean_json_text` 去除可能的 ```json``` 代码块标记。
4. `json.loads` 解析后，用 Pydantic `output_model.model_validate(data)` 校验。
5. 返回结构化 Pydantic 对象。

> 这是所有 Agent 与 LLM 交互的统一入口，确保返回值结构可靠。

## 6. 数据模型（Schemas）

### 6.1 输入 `TextbookInput`

| 字段 | 类型 | 说明 |
|---|---|---|
| `subject` | str | 学科 |
| `grade` | str | 年级 |
| `unit` | Optional[str] | 单元 |
| `lesson_title` | str | 课时标题 |
| `duration` | str | 课时长度（默认 `1课时`） |
| `textbook_content` | Optional[str] | 课本原文 |

### 6.2 课本抽取 `ExtractedTextbook`

| 字段 | 类型 | 说明 |
|---|---|---|
| `lesson_title` | str | 课时标题 |
| `knowledge_points` | List[KnowledgePoint] | 核心知识点（含原文片段） |
| `examples` | List[ExampleItem] | 例题 |
| `exercises` | List[ExerciseItem] | 习题 |
| `key_terms` | List[str] | 关键术语 |
| `summary` | str | 摘要 |

### 6.3 教案输出 `LessonPlanOutput`

```
LessonPlanOutput
├── lesson_title: str
├── teaching_objectives: TeachingObjective (knowledge / process / emotion)
├── key_difficult_points: KeyDifficultPoints (key_point / difficult_point)
└── teaching_design: TeachingDesign
    ├── pre_class_prep: List[str]
    ├── teaching_process: List[TeachingStage]
    │   ├── stage_name: str
    │   ├── steps: List[str]
    │   ├── design_intent: str
    │   ├── student_presets: Optional[List[str]]
    │   └── teacher_summary: Optional[str]
    ├── blackboard_design: str
    ├── homework: List[str]
    └── teaching_reflection: Optional[str]
```

### 6.4 审核 `ReviewResult`

| 字段 | 类型 | 说明 |
|---|---|---|
| `pass_review` | bool | 是否通过 |
| `score` | int | 0-100 评分 |
| `issues` | List[ReviewIssue] | 问题列表（category/stage/description/suggestion） |
| `overall_comment` | str | 总体意见 |

审核维度 `category`：
- `content_source`：内容是否来源于课本
- `format`：5 环节完整性、设计意图、学情预设
- `objective_alignment`：目标一致性

## 7. Agent 状态图（LangGraph）

### 7.1 全局状态 `AgentState`

`app/agents/state.py` 中定义的 `TypedDict`，在 Agent 间流转的共享状态：

| 字段 | 说明 |
|---|---|
| `textbook_input` | 原始用户输入 |
| `extracted_textbook` | 课本抽取结果 |
| `teaching_objectives` | 三维教学目标 |
| `key_difficult_points` | 重点难点 |
| `teaching_stages` | 教学过程各环节 |
| `blackboard_design` | 板书设计 |
| `homework` | 作业列表 |
| `teaching_reflection` | 教学反思 |
| `final_output` | 最终输出 |
| `review_pass` | 审核是否通过 |
| `review_feedback` | 审核反馈 |
| `revision_count` | 修改轮次计数 |

### 7.2 流程编排 `app/agents/graph.py`

```
              ┌───────────────────┐
              │ textbook_parser   │  课本解析 + 知识点抽取
              └────────┬──────────┘
                       ▼
              ┌───────────────────┐
              │ objective         │  三维教学目标
              └────────┬──────────┘
                       ▼
              ┌───────────────────┐
              │ key_difficult     │  教学重点 & 难点
              └────────┬──────────┘
                       ▼
              ┌───────────────────┐
              │ process           │  教学过程（5环节）+ 板书 + 作业 + 反思
              └────────┬──────────┘
                       ▼
              ┌───────────────────┐
              │ reviewer          │  教案审核
              └────────┬──────────┘
                       ▼
              ╔═══════════════════╗
        pass  ║  review_route      ║
        或超轮║  (条件路由)         ║
              ╚═════╤═══════╤═════╝
              pass  │       │ revise
                    ▼       ▼
                   END    process (回到教学过程重新生成)
```

**关键参数**：`MAX_REVISIONS = 2`（最多修改 2 轮，防止死循环）。

**路由逻辑 `_review_route`**：
- `review_pass == True` → `end`
- `revision_count >= 2` → `end`
- 否则 → `revise`（回到 `process` 重新生成，此时 prompt 会带上审核反馈）

## 8. 各 Agent 实现

### 8.1 `textbook_parser_agent` — 课本解析 Agent

```python
def textbook_parser_agent(state):
    extracted = extract_knowledge(state["textbook_input"].textbook_content)
    return {"extracted_textbook": extracted}
```

调用 `tools/knowledge_extractor.py` 中的 `extract_knowledge`：
- 用 LLM 从课本原文中抽取课时标题、知识点（含原文片段）、例题、习题、关键术语、摘要。
- 系统提示词强调"严格来源于课本原文，不得编造"。

### 8.2 `objective_agent` & `key_difficult_agent` — 目标与重难点

两个独立函数，均基于知识点列表调用 `invoke_structured_llm`：

- **`objective_agent`**：生成三维目标（知识与技能 / 过程与方法 / 情感态度与价值观），prompt 中注入年级与学科。
- **`key_difficult_agent`**：生成教学重点与难点。

### 8.3 `process_agent` — 教学过程设计 Agent

- 系统提示词强制输出包含 5 个固定环节的 JSON：情境导入、探究新知、实际运用、总结提升、作业设计。
- 要求每个环节包含 `design_intent`（设计意图），探究环节必须有 `student_presets`（学情预设）。
- **修改模式**：当 `state` 中存在 `review_feedback.issues` 时，将审核意见注入 prompt，要求重新生成完整教案。
- 每执行一次 `revision_count += 1`。

### 8.4 `reviewer_agent` — 教案审核 Agent

- 将课本知识点（作为审核依据）、教学目标、重难点、教学过程全部传入 LLM。
- 按 3 个维度审核并评分：
  - 90-100：优秀，通过
  - 70-89：合格，通过
  - 0-69：不通过，需修改
- 返回 `review_pass` 与 `review_feedback`（含问题列表与修改建议）。

## 9. 工具层（Tools）

### 9.1 `textbook_parser.py` — 文件解析

按文件后缀分发：

| 格式 | 解析方式 |
|---|---|
| `.pdf` | `pypdf.PdfReader` 逐页提取文本 |
| `.docx/.doc` | `python-docx` 提取段落文本 |
| `.txt/.md` | 按编码顺序尝试解码（utf-8-sig → utf-8 → gbk → gb18030 → utf-16 → big5） |
| 图片 | 调用 `ocr_image` 进行视觉 OCR |

提供两个入口：
- `parse_textbook(file_path)`：从文件路径解析
- `parse_textbook_bytes(content, filename)`：从内存字节解析（用于 HTTP 上传）

### 9.2 `knowledge_extractor.py` — 知识点抽取

使用 `get_llm()` + `ChatPromptTemplate` 调用文本模型，要求输出符合 `ExtractedTextbook` 结构的 JSON。

### 9.3 `image_ocr.py` — 图片 OCR

使用 `get_vision_llm()`（视觉模型），将图片以 base64 data URL 形式传入 `HumanMessage`，要求按排版顺序输出识别文字。

## 10. 请求完整链路示例

```
1. 前端 POST /api/parse-file (上传 PDF)
   → parse_textbook_bytes → pypdf 提取文本
   ← 返回 { filename, content }

2. 前端 POST /api/generate { subject, grade, lesson_title, textbook_content, ... }
   → build_graph() → graph.invoke({"textbook_input": input})
     2.1 textbook_parser_agent: extract_knowledge → extracted_textbook
     2.2 objective_agent: 三维目标
     2.3 key_difficult_agent: 重点难点
     2.4 process_agent: 5 环节教学过程 + 板书 + 作业 + 反思
     2.5 reviewer_agent: 审核
         ├─ pass → END
         └─ not pass & revision < 2 → process_agent (带 feedback 重新生成) → reviewer → ...
   ← 返回 LessonPlanOutput JSON
```

## 11. 设计要点总结

1. **多 Agent 分工明确**：解析、目标、重难点、过程、审核各司其职，便于单独优化 prompt。
2. **审核-修改闭环**：通过条件路由实现"生成→审核→修改"循环，最多 2 轮，兼顾质量与效率。
3. **结构化输出保障**：所有 LLM 返回均通过 Pydantic 模型校验，避免格式错误。
4. **多格式课本输入**：支持 PDF、Word、纯文本、图片（OCR），覆盖常见教学素材。
5. **内容溯源约束**：知识点保留 `source_excerpt` 原文片段，审核时作为"是否编造"的依据。
