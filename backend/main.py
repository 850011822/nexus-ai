"""
Nexus-AI 主入口 - FastAPI服务 + WebSocket实时通信
"""
import asyncio
import json
import os
import sys
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger
import sqlite3

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scheduler import TaskScheduler
from core.agent_team import AgentTeam
from core.memory import MemorySystem

# ==================== 配置 ====================

# 日志配置
LOG_DIR = Path(__file__).parent.parent / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger.add(
    LOG_DIR / "nexus_ai_{time}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO"
)

# 数据库
DB_PATH = Path(__file__).parent.parent / "data" / "nexus_ai.db"

# ==================== 数据模型 ====================

class TaskRequest(BaseModel):
    task: str
    mode: str = "auto"  # auto, research, develop, analyze

class SystemStatus(BaseModel):
    status: str
    uptime: float
    active_agents: int
    tasks_completed: int
    current_task: Optional[str] = None

# ==================== 应用初始化 ====================

app = FastAPI(title="Nexus-AI API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
class AppState:
    def __init__(self):
        self.running = False
        self.start_time = datetime.now()
        self.agent_team: Optional[AgentTeam] = None
        self.scheduler: Optional[TaskScheduler] = None
        self.memory: Optional[MemorySystem] = None
        self.active_tasks: Dict[str, Any] = {}
        self.websocket_connections: List[WebSocket] = []

        # 初始化数据库
        self.init_db()

    def init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()

        # 任务记录表
        c.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            status TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )''')

        # 系统日志表
        c.execute('''CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 系统状态表
        c.execute('''CREATE TABLE IF NOT EXISTS system_status (
            id INTEGER PRIMARY KEY,
            status TEXT,
            uptime REAL,
            tasks_completed INTEGER DEFAULT 0
        )''')

        conn.commit()
        conn.close()

state = AppState()

# ==================== WebSocket 广播 ====================

async def broadcast_to_websockets(message: dict):
    """广播消息到所有WebSocket连接"""
    message_str = json.dumps(message)
    disconnected = []

    for ws in state.websocket_connections:
        try:
            await ws.send_text(message_str)
        except Exception:
            disconnected.append(ws)

    # 清理断开的连接
    for ws in disconnected:
        state.websocket_connections.remove(ws)

async def log_to_all(message: str, level: str = "info"):
    """日志记录并广播"""
    logger.info(message)

    # 保存到数据库
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("INSERT INTO logs (level, message) VALUES (?, ?)", (level, message))
    conn.commit()
    conn.close()

    # 广播
    await broadcast_to_websockets({
        "type": "log",
        "level": level,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })

# ==================== API 路由 ====================

@app.get("/")
async def root():
    return {"message": "Nexus-AI API Running", "version": "1.0.0"}

@app.get("/status")
async def get_status() -> SystemStatus:
    """获取系统状态"""
    uptime = (datetime.now() - state.start_time).total_seconds()

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
    tasks_completed = c.fetchone()[0]
    conn.close()

    return SystemStatus(
        status="running" if state.running else "stopped",
        uptime=uptime,
        active_agents=len(state.active_tasks),
        tasks_completed=tasks_completed,
        current_task=list(state.active_tasks.keys())[0] if state.active_tasks else None
    )

@app.post("/tasks")
async def create_task(request: TaskRequest):
    """创建新任务"""
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    await log_to_all(f"📝 新任务创建: {request.task}")

    # 保存到数据库
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (task_name, status) VALUES (?, ?)",
        (request.task, "running")
    )
    task_db_id = c.lastrowid
    conn.commit()
    conn.close()

    # 更新状态
    state.active_tasks[task_id] = {
        "task": request.task,
        "mode": request.mode,
        "db_id": task_db_id,
        "start_time": datetime.now()
    }

    # 广播更新
    await broadcast_to_websockets({
        "type": "task_started",
        "task_id": task_id,
        "task": request.task,
        "timestamp": datetime.now().isoformat()
    })

    # 在后台执行任务
    asyncio.create_task(execute_task(task_id, request.task, request.mode))

    return {"task_id": task_id, "status": "started"}

@app.get("/tasks")
async def get_tasks():
    """获取所有任务"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT id, task_name, status, created_at, completed_at FROM tasks ORDER BY created_at DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()

    tasks = []
    for row in rows:
        tasks.append({
            "id": row[0],
            "name": row[1],
            "status": row[2],
            "created_at": row[3],
            "completed_at": row[4]
        })

    return tasks

@app.get("/logs")
async def get_logs(limit: int = 100):
    """获取系统日志"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute(f"SELECT level, message, timestamp FROM logs ORDER BY timestamp DESC LIMIT {limit}")
    rows = c.fetchall()
    conn.close()

    logs = []
    for row in rows:
        logs.append({
            "level": row[0],
            "message": row[1],
            "timestamp": row[2]
        })

    return logs

@app.post("/start")
async def start_system():
    """启动AI系统"""
    if state.running:
        return {"message": "系统已经在运行中"}

    state.running = True
    await log_to_all("🚀 Nexus-AI 系统启动!")

    # 初始化AI团队
    if not state.agent_team:
        state.agent_team = AgentTeam()

    # 初始化调度器
    if not state.scheduler:
        state.scheduler = TaskScheduler(state.agent_team)

    # 初始化记忆系统
    if not state.memory:
        state.memory = MemorySystem()

    # 启动定时任务
    asyncio.create_task(state.scheduler.start())

    return {"message": "系统启动成功"}

@app.post("/stop")
async def stop_system():
    """停止AI系统"""
    state.running = False

    if state.scheduler:
        state.scheduler.stop()

    await log_to_all("🛑 Nexus-AI 系统已停止")

    return {"message": "系统已停止"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时通信"""
    await websocket.accept()
    state.websocket_connections.append(websocket)

    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "message": "已连接到Nexus-AI实时监控",
            "timestamp": datetime.now().isoformat()
        })

        # 保持连接
        while True:
            data = await websocket.receive_text()
            # 可以处理客户端发来的消息
            pass

    except WebSocketDisconnect:
        state.websocket_connections.remove(websocket)

# ==================== 任务执行 ====================

async def execute_task(task_id: str, task: str, mode: str):
    """执行AI任务"""
    try:
        await log_to_all(f"🔄 开始执行任务: {task}")

        # 执行任务
        result = await state.agent_team.execute_task(task, mode)

        # 更新数据库
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute(
            "UPDATE tasks SET status = ?, result = ?, completed_at = ? WHERE id = ?",
            ("completed", str(result), datetime.now(), state.active_tasks[task_id]["db_id"])
        )
        conn.commit()
        conn.close()

        # 完成任务
        await log_to_all(f"✅ 任务完成: {task}")

        # 保存结果到记忆
        if state.memory:
            state.memory.save_task_result(task, result)

        # 广播完成
        await broadcast_to_websockets({
            "type": "task_completed",
            "task_id": task_id,
            "result": str(result)[:500],
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        await log_to_all(f"❌ 任务失败: {str(e)}", "error")

        # 更新数据库
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute(
            "UPDATE tasks SET status = ?, result = ? WHERE id = ?",
            ("failed", str(e), state.active_tasks[task_id]["db_id"])
        )
        conn.commit()
        conn.close()

    finally:
        # 清理状态
        if task_id in state.active_tasks:
            del state.active_tasks[task_id]

# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    logger.info("Nexus-AI Backend Starting...")
    await log_to_all("🔵 Nexus-AI Backend 启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理"""
    logger.info("Nexus-AI Backend Shutting Down...")
    state.running = False

# ==================== 主程序 ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
