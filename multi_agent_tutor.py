import json
import os
import datetime
from typing import AsyncGenerator, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Body, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
from database.manager import DatabaseManager

# ==========================================
# 核心配置
# ==========================================
API_KEY = os.getenv("DEEPSEEK_API_KEY", "your_api_key_here")
BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"

TEACHER_CONFIG = {
    "username": "T001",
    "password": "123456",
    "name": "张老师"
}

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
app = FastAPI(title="K12 智能教育系统 - 模块化重构版")
db = DatabaseManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 数据模型
# ==========================================
class LoginRequest(BaseModel):
    role: str
    username: str
    password: Optional[str] = None

class CreateStudentRequest(BaseModel):
    student_id: str
    name: str
    tags: List[str]

class ChatRequest(BaseModel):
    student_id: str
    message: str

class ChatEndRequest(BaseModel):
    student_id: str
    history: List[dict]

# 权限校验中间件
def verify_teacher_token(x_token: str = Header(None)):
    if x_token != "TEACHER_SECRET_TOKEN":
        raise HTTPException(status_code=403, detail="无权执行此操作")
    return True

# ==========================================
# 接口实现
# ==========================================
@app.post("/auth/login")
async def login(req: LoginRequest):
    if req.role == "teacher":
        if req.username == TEACHER_CONFIG["username"] and req.password == TEACHER_CONFIG["password"]:
            return {
                "status": "success", 
                "role": "teacher", 
                "name": TEACHER_CONFIG["name"],
                "token": "TEACHER_SECRET_TOKEN"
            }
        raise HTTPException(status_code=401, detail="工号或密码错误")
    
    elif req.role == "student":
        student_data = db.read_student(req.password)
        if student_data and student_data["basic_info"]["name"] == req.username:
            return {"status": "success", "role": "student", "name": req.username, "student_id": req.password}
        raise HTTPException(status_code=401, detail="姓名或学号不匹配")
    
    raise HTTPException(status_code=400, detail="无效的角色")

@app.get("/teacher/students", dependencies=[Depends(verify_teacher_token)])
async def list_students():
    return db.list_students()

@app.post("/teacher/students", dependencies=[Depends(verify_teacher_token)])
async def add_student(req: CreateStudentRequest):
    success, msg = db.create_student(req.student_id, req.name, req.tags)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}

@app.delete("/teacher/students/{student_id}", dependencies=[Depends(verify_teacher_token)])
async def delete_student(student_id: str):
    success, msg = db.delete_student(student_id, operator="张老师")
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}

@app.post("/teacher/analysis", dependencies=[Depends(verify_teacher_token)])
async def analyze_student(student_id: str = Body(..., embed=True)):
    student_data = db.read_student(student_id)
    if not student_data:
        raise HTTPException(status_code=404, detail="找不到该学生")
    
    prompt = f"分析以下学生档案并给出诊断报告：{json.dumps(student_data, ensure_ascii=False)}"
    response = client.chat.completions.create(model=MODEL_NAME, messages=[{"role": "user", "content": prompt}])
    return {"analysis": response.choices[0].message.content}

@app.post("/teacher/recommendation", dependencies=[Depends(verify_teacher_token)])
async def get_recommendation(student_id: str = Body(..., embed=True)):
    student_data = db.read_student(student_id)
    if not student_data:
        raise HTTPException(status_code=404, detail="找不到该学生")
    
    # 获取最近 5 条记录
    logs = student_data.get("weakness_log", [])
    recent_logs = logs[-5:] if logs else []
    
    context = {
        "basic_info": student_data.get("basic_info"),
        "recent_weaknesses": recent_logs
    }

    prompt = f"""
    作为一名资深教育心理学专家和学科带头人，请基于以下学生档案（特别是最近的弱点日志）生成一份高水准的教学建议。

    学生背景及近期记录：
    {json.dumps(context, ensure_ascii=False)}

    要求输出以下三个部分，保持学术严谨，禁止使用空洞的词汇（如“努力学习”、“加油”等）：
    1. **当前认知水平评估**：基于最近的弱点记录，精准刻画学生目前的思维深度、知识盲区及认知障碍点。
    2. **预测学习难点**：预测在接下来的进阶学习中，该生最可能在哪些具体概念或逻辑环节遇到瓶颈。
    3. **推荐教学方案**：提供具有可操作性的干预策略。例如：建议先通过具体的物理实验或案例建立感性认识，再引入形式化的数学推导。

    请使用 Markdown 格式输出。
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一位严谨的教育专家，输出内容需具备专业深度。"},
                {"role": "user", "content": prompt}
            ]
        )
        return {"recommendation": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 生成建议失败: {str(e)}")

@app.post("/chat")
async def chat_endpoint(req: ChatRequest, background_tasks: BackgroundTasks):
    return StreamingResponse(
        stream_socratic_reply(req.student_id, req.message, background_tasks),
        media_type="text/event-stream"
    )

async def stream_socratic_reply(student_id: str, user_input: str, background_tasks: BackgroundTasks):
    system_prompt = "你是一名苏格拉底式导师。绝不直接给答案，通过确认逻辑、揭示矛盾、追问引导来启发学生。"
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}],
            stream=True
        )
        full_ai_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_ai_response += content
                yield content
    except Exception as e:
        yield f"【连接中断】: {str(e)}"

@app.post("/chat/end")
async def end_chat(req: ChatEndRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_profiler_agent, req.student_id, req.history)
    return {"status": "processing"}

async def run_profiler_agent(student_id: str, history: List[dict]):
    if not history:
        return

    # 构造 Profiler Agent 的提示词
    chat_content = "\n".join([f"{m['role']}: {m['content']}" for m in history])
    prompt = f"""
    请分析以下师生对话内容：
    {chat_content}

    任务：
    1. 总结本次对话涉及的 3 个核心知识点（用简短的词语表示）。
    2. 识别学生在哪个环节出现了逻辑断裂或理解偏差。

    请严格按以下 JSON 格式输出，不要包含任何其他文字：
    {{
        "topic": "知识点1, 知识点2, 知识点3",
        "logic_gap": "具体逻辑断裂点的描述"
    }}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": "你是一名资深教育专家，擅长诊断学生思维障碍。"}, 
                      {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        # 写入档案
        student_data = db.read_student(student_id)
        if student_data:
            new_log = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "topic": analysis.get("topic", "未知知识点"),
                "logic_gap": analysis.get("logic_gap", "未识别到明显逻辑断裂")
            }
            if "weakness_log" not in student_data:
                student_data["weakness_log"] = []
            
            student_data["weakness_log"].append(new_log)
            db.write_student(student_id, student_data, operator="ProfilerAgent")
            
    except Exception as e:
        print(f"Profiler Agent Error: {e}")

@app.get("/health")
async def health():
    return {"status": "online"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
