# LessonSynth — 多智能体教案生成系统

基于 **LangGraph** 的多 Agent 教学活动设计平台。输入课本内容（文本 / PDF / Word / 图片 OCR），自动生成包含教学目标、重点难点、教学过程（5 环节）、板书、作业、反思的完整结构化教案，并内置审核-修改闭环，最多两轮迭代优化。

---

## ✨ 核心特性

- 🤖 **多 Agent 协作**：课本解析、目标生成、重难点分析、过程设计、教案审核，每个环节独立 Agent 各司其职
- 🔁 **审核-修改闭环**：教案自动审核，发现问题后带着反馈重新生成，最多迭代 2 轮
- 📚 **多格式课本输入**：支持 PDF / DOCX / TXT / Markdown / 图片（视觉 OCR）
- 📝 **内容溯源约束**：每个知识点保留原文片段，审核时校验是否编造课本外内容
- 📤 **多格式导出**：前端一键导出 PDF / DOCX / Markdown
- 🎨 **现代化 UI**：Vue 3 + Element Plus

---

## 🏗️ 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | FastAPI + Uvicorn |
| 多 Agent 编排 | LangGraph + LangChain |
| LLM | DeepSeek（通过 OpenAI 兼容接口接入） |
| 文档解析 | pypdf / python-docx |
| 视觉 OCR | DeepSeek 视觉模型 |
| 前端框架 | Vue 3 + Vite |
| UI 组件 | Element Plus |
| PDF 导出 | html2canvas + jsPDF |
| Word 导出 | docx |

---

## 📁 项目结构

```
LessonSynth/
├── app/                        # 后端（Python / FastAPI）
│   ├── main.py                 # 应用入口
│   ├── config.py               # 全局配置
│   ├── api/
│   │   └── lesson.py           # HTTP 接口
│   ├── agents/
│   │   ├── graph.py            # LangGraph 状态图编排
│   │   ├── state.py            # 全局状态定义
│   │   ├── llm_helper.py       # 结构化 LLM 调用
│   │   ├── textbook_parser_agent.py
│   │   ├── objective_agent.py
│   │   ├── process_agent.py
│   │   └── reviewer_agent.py
│   ├── tools/
│   │   ├── textbook_parser.py  # 多格式文件解析
│   │   ├── knowledge_extractor.py
│   │   └── image_ocr.py
│   ├── schemas/                # Pydantic 数据模型
│   └── utils/llm.py            # LLM 客户端工厂
├── frontend/                   # 前端（Vue 3）
│   ├── src/
│   │   ├── api/lesson.js
│   │   ├── utils/export.js     # PDF / DOCX / MD 导出
│   │   ├── App.vue
│   │   └── main.js
│   └── vite.config.js
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- 一个 **DeepSeek API Key**（[在这里申请](https://platform.deepseek.com/)）

### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/LessonSynth.git
cd LessonSynth
```

### 2. 后端配置与启动

```bash
# 创建虚拟环境
python -m venv venv
# Windows 激活
venv\Scripts\activate
# macOS / Linux 激活
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env
# 然后编辑 .env，把 DEEPSEEK_API_KEY 改成你自己的
```

启动后端服务：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后访问 http://localhost:8000/docs 查看 Swagger API 文档。

### 3. 前端配置与启动

```bash
cd frontend
npm install
npm run dev
```

前端启动后访问 http://localhost:5173 。Vite 已配置 `/api` 反向代理到后端 `localhost:8000`，无需额外配置。

---

## 📖 使用流程

1. 打开 http://localhost:5173
2. 填写学科、年级、课时标题等基本信息
3. **课本内容**可选择：
   - 直接粘贴文本
   - 点击上传按钮，上传 PDF / Word / TXT / 图片
4. 点击 **「生成教案」**，等待 10~30 秒
5. 生成完成后可查看完整教案，并通过右上角下拉菜单导出 **PDF / Word / Markdown**

---

## 🔄 Agent 流程图

```
textbook_parser ──→ objective ──→ key_difficult ──→ process ──→ reviewer
   课本解析            教学目标         重点难点          教学过程        教案审核
                                                                     │
                                                        ┌────────────┼────────────┐
                                                        ▼                         ▼
                                                      通过/超轮次              revise
                                                        │                         │
                                                        ▼                         ▼
                                                       END                  process（带反馈重新生成）
```

最多修改 2 轮，防止死循环。

---

## 🛠️ API 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/parse-file` | 上传并解析课本文件 |
| POST | `/api/generate` | 生成完整教案 |
| GET | `/api/generate/info` | 获取流程说明 |
| GET | `/` | 服务状态 |
| GET | `/health` | 健康检查 |

详细参数与返回值见后端 Swagger：http://localhost:8000/docs

---

## 📄 导出格式说明

| 格式 | 技术方案 | 特点 |
|---|---|---|
| PDF | html2canvas + jsPDF | 基于 Canvas 渲染，中文完美支持，自动分页 |
| Word (DOCX) | docx 库 | 原生 Word 文档，可编辑 |
| Markdown | 字符串拼接 | 纯文本，通用 |

---

## ⚙️ 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | — | **必填**，DeepSeek API Key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | OpenAI 兼容接口地址 |
| `DEEPSEEK_MODEL` | `deepseek-v4-pro` | 文本生成模型 |
| `DEEPSEEK_VISION_MODEL` | `deepseek-chat` | 视觉 OCR 模型 |
| `APP_HOST` | `0.0.0.0` | 后端监听地址 |
| `APP_PORT` | `8000` | 后端端口 |

---

## 📝 License

MIT
