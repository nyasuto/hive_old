#!/usr/bin/env python3
"""
Hive Dashboard API - FastAPI + WebSocket Real-time Backend
Issue #132 - Phase 3A: Browser-based Real-time Dashboard Implementation

WebSocketとREST APIを組み合わせたリアルタイムダッシュボード基盤
"""

import asyncio
import json
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.hive_watch import HiveWatch
from scripts.worker_communication import WorkerCommunicator


class WorkerStatus(BaseModel):
    """Worker状態モデル"""

    name: str
    status: str  # active, idle, working, error
    current_task: str | None = None
    emoji: str
    last_activity: str | None = None
    progress: int | None = None


class CommunicationMessage(BaseModel):
    """通信メッセージモデル"""

    timestamp: str
    source: str
    target: str
    message_type: str
    message: str
    session_id: str | None = None


class SessionInfo(BaseModel):
    """セッション情報モデル"""

    session_id: str
    start_time: str
    duration: str | None = None
    active_workers: list[str]
    message_count: int
    status: str  # active, completed, error


class DashboardData(BaseModel):
    """ダッシュボード統合データモデル"""

    timestamp: str
    workers: list[WorkerStatus]
    recent_messages: list[CommunicationMessage]
    current_session: SessionInfo | None = None
    performance_metrics: dict[str, Any]


class ConnectionManager:
    """WebSocket接続管理"""

    def __init__(self) -> None:
        self.active_connections: set[WebSocket] = set()
        self.last_data: DashboardData | None = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

        # 初期データを送信
        if self.last_data:
            await websocket.send_text(self.last_data.model_dump_json())

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast(self, data: DashboardData) -> None:
        """全接続クライアントにデータ配信"""
        self.last_data = data
        message = data.model_dump_json()

        # 切断された接続を削除しながらブロードキャスト
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.add(connection)

        self.active_connections -= disconnected


class HiveDashboardCollector:
    """Hiveシステムからのデータ収集"""

    def __init__(self) -> None:
        self.communicator = WorkerCommunicator()
        self.hive_watch = HiveWatch()
        self.worker_emojis = {
            "queen": "👑",
            "developer": "👨‍💻",
            "tester": "🧪",
            "analyzer": "🔍",
            "documenter": "📝",
            "reviewer": "👀",
            "beekeeper": "📋",
        }

    async def collect_dashboard_data(self) -> DashboardData:
        """ダッシュボード用データを収集"""
        timestamp = datetime.now().isoformat()

        # Worker状態収集
        workers = await self._collect_worker_status()

        # 最近の通信メッセージ収集
        recent_messages = self._collect_recent_messages()

        # 現在セッション情報
        current_session = self._get_current_session_info()

        # パフォーマンス指標
        performance_metrics = self._calculate_performance_metrics()

        return DashboardData(
            timestamp=timestamp,
            workers=workers,
            recent_messages=recent_messages,
            current_session=current_session,
            performance_metrics=performance_metrics,
        )

    async def _collect_worker_status(self) -> list[WorkerStatus]:
        """Worker状態を収集"""
        status_data = self.communicator.monitor_worker_status()
        workers = []

        if status_data.get("session_active", False):
            worker_info = status_data.get("workers", {})

            for worker_name, info in worker_info.items():
                is_active = info.get("pane_active", False)
                status = "active" if is_active else "idle"

                worker = WorkerStatus(
                    name=worker_name,
                    status=status,
                    emoji=self.worker_emojis.get(worker_name, "🐝"),
                    last_activity=datetime.now().strftime("%H:%M:%S")
                    if is_active
                    else None,
                )
                workers.append(worker)
        else:
            # セッション非アクティブの場合、デフォルトWorker一覧
            for worker_name, emoji in self.worker_emojis.items():
                worker = WorkerStatus(name=worker_name, status="inactive", emoji=emoji)
                workers.append(worker)

        return workers

    def _collect_recent_messages(self, limit: int = 10) -> list[CommunicationMessage]:
        """最近の通信メッセージを収集"""
        project_root = Path(__file__).parent.parent.parent.parent
        log_file = project_root / "logs" / "hive_communications.log"
        messages: list[CommunicationMessage] = []

        if not log_file.exists():
            return messages

        try:
            with open(log_file, encoding="utf-8") as f:
                lines = f.readlines()
                recent_lines = lines[-limit:] if len(lines) > limit else lines

                for line in recent_lines:
                    try:
                        log_entry = json.loads(line.strip())

                        message = CommunicationMessage(
                            timestamp=log_entry["timestamp"],
                            source=log_entry["source"],
                            target=log_entry["target"],
                            message_type=log_entry.get("message_type")
                            or log_entry.get("event_type", "unknown"),
                            message=log_entry["message"][:100] + "..."
                            if len(log_entry["message"]) > 100
                            else log_entry["message"],
                            session_id=log_entry.get("session_id"),
                        )
                        messages.append(message)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading communication logs: {e}")

        return messages

    def _get_current_session_info(self) -> SessionInfo | None:
        """現在のセッション情報を取得"""
        status_data = self.communicator.monitor_worker_status()

        if not status_data.get("session_active", False):
            return None

        # 簡易セッション情報生成
        active_workers = [
            name
            for name, info in status_data.get("workers", {}).items()
            if info.get("pane_active", False)
        ]

        session_info = SessionInfo(
            session_id=f"session_{int(time.time())}",
            start_time=datetime.now().strftime("%H:%M:%S"),
            active_workers=active_workers,
            message_count=len(self._collect_recent_messages(100)),
            status="active",
        )

        return session_info

    def _calculate_performance_metrics(self) -> dict[str, Any]:
        """パフォーマンス指標を計算"""
        messages = self._collect_recent_messages(50)

        if not messages:
            return {
                "efficiency": 0,
                "avg_response_time": 0,
                "message_rate": 0,
                "active_workers": 0,
            }

        # 簡易パフォーマンス計算
        recent_count = len(
            [
                m
                for m in messages
                if (datetime.now() - datetime.fromisoformat(m.timestamp)).seconds < 300
            ]
        )

        return {
            "efficiency": min(95, recent_count * 10),  # 簡易効率算出
            "avg_response_time": 2.3,  # 固定値（後で実装）
            "message_rate": recent_count / 5,  # 5分間のメッセージレート
            "active_workers": len({m.source for m in messages}),
        }


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """アプリケーションライフサイクル管理"""
    # 起動時処理
    print("🐝 Hive Dashboard API starting...")
    print("📊 WebSocket broadcast task starting...")

    # バックグラウンドでデータ配信開始
    broadcast_task = asyncio.create_task(broadcast_dashboard_data())

    yield

    # 終了時処理
    print("👋 Hive Dashboard API shutting down...")
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass


# FastAPIアプリケーション初期化
app = FastAPI(
    title="🐝 Hive Dashboard API",
    description="Real-time monitoring dashboard for Hive distributed system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket接続管理とデータ収集
manager = ConnectionManager()
collector = HiveDashboardCollector()

# 静的ファイル配信
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def dashboard_home() -> HTMLResponse:
    """ダッシュボードホーム画面"""
    html_file = Path(__file__).parent.parent / "templates" / "index.html"
    if html_file.exists():
        with open(html_file, encoding="utf-8") as f:
            return HTMLResponse(f.read())

    # デフォルトHTML（開発用）
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🐝 Hive Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="/static/css/dashboard.css">
    </head>
    <body>
        <div id="app">
            <h1>🐝 Hive Dashboard Loading...</h1>
            <p>WebSocket接続中...</p>
        </div>
        <script src="/static/js/dashboard.js"></script>
    </body>
    </html>
    """)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocketリアルタイム通信エンドポイント"""
    await manager.connect(websocket)

    try:
        # クライアントからのメッセージを待機（keep-alive用）
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/status")
async def get_system_status() -> dict[str, Any]:
    """システム状態API"""
    data = await collector.collect_dashboard_data()
    return {
        "status": "active" if data.current_session else "inactive",
        "timestamp": data.timestamp,
        "worker_count": len(data.workers),
        "active_workers": len([w for w in data.workers if w.status == "active"]),
        "message_count": len(data.recent_messages),
    }


@app.get("/api/workers")
async def get_workers() -> dict[str, Any]:
    """Worker一覧API"""
    data = await collector.collect_dashboard_data()
    return {"workers": [w.model_dump() for w in data.workers]}


@app.get("/api/messages")
async def get_recent_messages(limit: int = 20) -> dict[str, Any]:
    """最近のメッセージAPI"""
    messages = collector._collect_recent_messages(limit)
    return {"messages": [m.model_dump() for m in messages]}


@app.get("/api/performance")
async def get_performance_metrics() -> dict[str, Any]:
    """パフォーマンス指標API"""
    data = await collector.collect_dashboard_data()
    return {"metrics": data.performance_metrics}


async def broadcast_dashboard_data() -> None:
    """定期的なダッシュボードデータ配信"""
    while True:
        try:
            if manager.active_connections:
                data = await collector.collect_dashboard_data()
                await manager.broadcast(data)
        except Exception as e:
            print(f"Error broadcasting data: {e}")

        await asyncio.sleep(1)  # 1秒間隔


if __name__ == "__main__":
    print("🚀 Starting Hive Dashboard Server...")
    print("📊 Dashboard: http://localhost:8002")
    print("🔌 WebSocket: ws://localhost:8002/ws")
    print("📡 API Docs: http://localhost:8002/docs")

    uvicorn.run(
        "dashboard_api:app", host="0.0.0.0", port=8002, reload=True, log_level="info"
    )
