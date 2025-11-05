from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, asyncio
from typing import Dict
from src.modules.initialize import Initialize

app = FastAPI()

origins = [
    "http://localhost:3000/",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class Request(BaseModel):
    text: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f" {user_id} connected")

    async def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f" {user_id} disconnected")

    async def send_personal_message(self, message: str, user_id: str, type_: str):
        websocket = self.active_connections.get(user_id)
        if websocket:
            res = {"response": message, "type": type_}
            await websocket.send_json(res)

    async def broadcast(self, message: str):
        for uid, ws in self.active_connections.items():
            await ws.send_text(message)

    async def keepalive(self, user_id: str):
        """Keep WebSocket alive with periodic pings"""
        websocket = self.active_connections.get(user_id)
        while websocket and websocket.client_state.name != "CLOSED":
            try:
                await asyncio.sleep(30)
                await websocket.send_json({"type": "ping"})
            except:
                break


manager = ConnectionManager()

class ManageQuery:
    def __init__(self) -> None:
        self.models = {}

    async def initialize(self, dbName: str, userId: str):
        file_path = os.path.join("uploads", userId, dbName)
        if userId not in self.models:
            self.models[userId] = {}
        if dbName not in self.models[userId]:
            models = Initialize(file_path, id=userId, dbname=dbName,manageConnection=manager)
            self.models[userId][dbName] = await models.init()

        pdfs = self.models[userId][dbName]
        await pdfs.analyze_page(chuck=300, over=1, max_chunck=500)
 
    async def askQuery(self, userid: str, dbName: str, q: str):
        print("dbName :",dbName)
        if not dbName:
            await manager.send_personal_message("No pdf mentioned",userid,"NoPdf")
            return
        try:
            if userid not in self.models or dbName not in self.models[userid]:
                await self.initialize(dbName, userid)

            async for ch in self.models[userid][dbName].query(q, 10):
                await manager.send_personal_message(ch, userid, "query")

        except Exception as e:
            print(f"Error Occurred: {e}")


manageQuery = ManageQuery()

def run_in_background_initialize(filename: str, user_id: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(manageQuery.initialize(filename, user_id))
    loop.close()

async def handle_message(user_id: str, data: Dict):
    _type = data.get("type")
    q = data.get("data")

    if _type == "query":
        pdf = data.get("pdf")
        await manageQuery.askQuery(user_id, pdf, q)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)

    asyncio.create_task(manager.keepalive(user_id))

    try:
        while True:
            data = await websocket.receive_json()
            await handle_message(user_id, data)

    except WebSocketDisconnect:
        await manager.disconnect(user_id)
    except Exception as e:
        print(f" WebSocket error: {e}")
        await manager.disconnect(user_id)

@app.post("/upload/")
async def uploadFile(user_id: str, file: UploadFile = File(...)):
    try:
        upload_dir = os.path.join("uploads", user_id)
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        print(f" Saving file to {file_path}")

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        await manager.send_personal_message(f"{file.filename} is received", user_id, "uploadResponse")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_in_background_initialize, file.filename, user_id)

        await manager.send_personal_message(f"{file.filename} is initialized", user_id, "PdfInitialize")

        return {"filename": file.filename, "size": len(content)}

    except Exception as e:
        print(" ERROR while saving file:", e)
        return {"error": str(e)}

@app.get("/items/{items:path}/")
async def get_ratio(items: str, q1: int, q2: int):
    result = q1 / q2
    return {"message": f"{items}-{result:.3f}"}


@app.get("/item/{items}/")
async def get_item(items: str):
    return {"message": f"{items}"}


@app.post("/process-text/")
async def process_text(req: Request):
    text = req.text
    print(f"📝 Received Text: {text}")
    return {"message": text.upper()}
