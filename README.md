# Socratic Education System v2 🎓

> **基于苏格拉底式启发教学法的 K12 智能教育 AI Agent 平台**

## 🌟 Project Vision

本平台致力于将古老的“苏格拉底式教学法”与现代大语言模型（LLM）技术相结合，为 K12 阶段的学生提供一个**不直接给出答案、而是通过追问引导思考**的智能陪伴环境。我们相信，教育的本质不是灌输，而是点燃。通过多智能体协作，平台能够精准捕捉学生的逻辑断裂点，并为教师提供具有深厚教育心理学背景的学情诊断与教学建议。

## 🚀 Core Features

- **🎭 多智能体协作流程 (Multi-Agent Collaboration)**
    - **Socratic Tutor Agent**: 核心对话机器人，严格遵循引导式教学，通过逻辑确认、揭示矛盾和连续追问来启发学生。
    - **Profiler Agent**: 对话结束后自动运行，深度复盘对话历史，提取核心知识点并识别认知障碍。
- **📊 动态学生画像回写 (Dynamic Student Profiling)**
    - 每次对话后，系统会自动将诊断出的“思维弱点”以结构化日志 (`weakness_log`) 形式回写至 JSON 数据库，实现学生认知状态的实时跟踪。
- **🧑‍🏫 教师端学情诊断与教学建议**
    - **一键分析报告**: 整合全量档案生成深度诊断。
    - **智能教学方案**: 基于最近 5 条弱点记录，预测学习难点并推荐具体的干预策略（如：先实验感性认知，再理论理性推导）。
- **💾 模块化文件数据库**
    - 基于线程安全（RLock）的 JSON 存储系统，确保在轻量级部署下依然具备强健的并发处理能力与审计追踪日志。

## 🛠 Installation & Setup

### 前置要求
- Python 3.10+
- DeepSeek API Key

### 1. 克隆并进入项目
```bash
git clone <your-repo-url>
cd 个人网站
```

### 2. 创建并激活虚拟环境
```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate # Windows
```

### 3. 安装依赖
```bash
pip install fastapi uvicorn openai pydantic marked
```

### 4. 配置 API Key
在 `multi_agent_tutor.py` 中修改以下配置：
```python
API_KEY = "您的 DeepSeek API Key"
```

### 5. 启动服务
```bash
python3 multi_agent_tutor.py
```
服务启动后，在浏览器中打开 `index.html` 即可开始体验。

## 📂 Project Structure

- `multi_agent_tutor.py`: 后端核心，包含所有 API 路由与 Agent 逻辑。
- `database/manager.py`: 数据库管理类，处理 JSON 读写与并发锁。
- `index.html`: 现代感 UI 界面，集成 Markdown 渲染与 KaTeX 公式支持。
- `data/students/`: 存放结构化的学生档案。
- `logs/`: 记录系统操作审计日志。

## 📄 License

本项目采用 [MIT 许可证](LICENSE)。您可以自由地使用、修改和分发。

---
*由 AI 驱动，为每一个孩子提供苏格拉底式的智慧启迪。*
