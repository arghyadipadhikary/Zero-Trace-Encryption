import os
import uuid
import json
import hashlib
import time
import asyncio
import shutil
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, BackgroundTasks, Form, Cookie, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# 1. Environment and Constants
load_dotenv()
MAX_FILE_SIZE = 650 * 1024 * 1024 
EXPIRATION_SECONDS = 10800 

# VERCEL FIX: Must use /tmp for write permissions
UPLOAD_DIR = "/tmp/ephemeral_storage"
os.makedirs(UPLOAD_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@asynccontextmanager
async def lifespan(app: FastAPI):
    async def cleanup_expired_files():
        while True:
            now = time.time()
            if os.path.exists(UPLOAD_DIR):
                for filename in os.listdir(UPLOAD_DIR):
                    file_path = os.path.join(UPLOAD_DIR, filename)
                    if os.path.isfile(file_path):
                        if (now - os.path.getmtime(file_path)) > EXPIRATION_SECONDS:
                            try: os.remove(file_path)
                            except: pass
            await asyncio.sleep(3600)
    task = asyncio.create_task(cleanup_expired_files())
    yield
    task.cancel()

app = FastAPI(title="ZeroTrace V2.3 - Advanced Recipient Pinning", lifespan=lifespan)

if os.path.exists(os.path.join(BASE_DIR, "static")):
    app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(
    request: Request, 
    file: UploadFile = File(...), 
    burn: bool = False
):
    content_length = request.headers.get('content-length')
    if content_length and int(content_length) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    file_id = str(uuid.uuid4())
    suffix = ".burn.bin" if burn else ".bin"
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{suffix}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"success": True, "fileId": file_id, "burned": burn}
    except Exception:
        if os.path.exists(file_path): os.remove(file_path)
        raise HTTPException(status_code=500, detail="Upload failed")
    expiry_timestamp = time.time() + EXPIRATION_SECONDS
    return {
        "success": True, 
        "fileId": file_id, 
        "burned": burn,
        "expiry": expiry_timestamp # Send this to the frontend
}

@app.get("/download/{file_id}")
async def download_file(
    request: Request, 
    file_id: str, 
    background_tasks: BackgroundTasks,
    response: Response,
    session_id: str = Cookie(None)
):
    # --- 1. IDENTITY CAPTURE ---
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(key="session_id", value=session_id, httponly=True, samesite="lax")

    # Generate Device Fingerprint (Hashed User-Agent)
    user_agent = request.headers.get("user-agent", "unknown")
    fingerprint = hashlib.sha256(user_agent.encode()).hexdigest()[:16]

    # Capture Network & Geo (Vercel Headers)
    user_ip = request.headers.get("x-forwarded-for", request.client.host).split(",")[0]
    user_country = request.headers.get("x-vercel-ip-country", "XX")
    user_city = request.headers.get("x-vercel-ip-city", "Unknown")

    # --- 2. FILE LOCATION ---
    target_path = None
    is_burn = False
    for f in os.listdir(UPLOAD_DIR):
        if f.startswith(file_id) and f.endswith(".bin"):
            target_path = os.path.join(UPLOAD_DIR, f)
            is_burn = ".burn.bin" in f
            break

    if not target_path or not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="Resource not found or already consumed")

    # --- 3. ADVANCED PINNING LOCK ---
    lock_path = os.path.join(UPLOAD_DIR, f"{file_id}.lock")
    
    current_identity = {
        "sid": session_id,
        "ip": user_ip,
        "fp": fingerprint,
        "geo": f"{user_city}, {user_country}"
    }

    if os.path.exists(lock_path):
        with open(lock_path, "r") as lf:
            original_identity = json.load(lf)
        
        # Verify Session, IP, and Device Fingerprint
        if (original_identity["sid"] != current_identity["sid"] or 
            original_identity["ip"] != current_identity["ip"] or 
            original_identity["fp"] != current_identity["fp"]):
            
            # Security Alert: Block access for mismatched identities
            raise HTTPException(
                status_code=403, 
                detail=f"SECURITY ALERT: Link locked to a different device or network. Access attempted from {current_identity['geo']}."
            )
    else:
        # First visitor pins the file to their identity profile
        with open(lock_path, "w") as lf:
            json.dump(current_identity, lf)

    # --- 4. CLEANUP ---
    def cleanup(paths: list):
        time.sleep(2)
        for path in paths:
            try:
                if os.path.exists(path): os.remove(path)
            except: pass

    if is_burn:
        background_tasks.add_task(cleanup, [target_path, lock_path])

    return FileResponse(path=target_path, media_type="application/octet-stream", filename="decrypted_asset.bin")