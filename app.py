import os
import uuid
import time
import asyncio
import shutil
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 1. FIX: Setup absolute paths for Vercel
base_dir = os.path.dirname(os.path.abspath(__file__))
# If your code is in /api/app.py, we go up one level to find folders
root_dir = os.path.abspath(os.path.join(base_dir, "..")) 

UPLOAD_DIR = os.path.join(root_dir, "ephemeral_storage")
os.makedirs(UPLOAD_DIR, exist_ok=True)

EXPIRATION_SECONDS = 10800  
MAX_FILE_SIZE = 650 * 1024 * 1024  

limiter = Limiter(key_func=get_remote_address)

async def cleanup_expired_files():
    """Background loop to clean up old files."""
    while True:
        now = time.time()
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    if (now - os.path.getmtime(file_path)) > EXPIRATION_SECONDS:
                        try:
                            os.remove(file_path)
                        except:
                            pass
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(cleanup_expired_files())
    yield
    task.cancel()

app = FastAPI(title="Secure E2EE Web Share", lifespan=lifespan)

# 2. FIX: Safe Static Files Mounting
static_path = os.path.join(root_dir, "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 3. FIX: Absolute Templates Path
templates_path = os.path.join(root_dir, "templates")
templates = Jinja2Templates(directory=templates_path)

@app.get("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
@limiter.limit("5/minute")
async def upload_file(request: Request, file: UploadFile = File(...), burn: bool = False):
    content_length = request.headers.get('content-length')
    if content_length and int(content_length) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    file_id = str(uuid.uuid4())
    suffix = ".burn.bin" if burn else ".bin"
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{suffix}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        actual_size = os.path.getsize(file_path)
        if actual_size > MAX_FILE_SIZE:
            os.remove(file_path)
            raise HTTPException(status_code=413, detail="File too large")
            
        return {"success": True, "fileId": file_id, "burned": burn}
    
    except Exception as e:
        if os.path.exists(file_path): os.remove(file_path)
        raise HTTPException(status_code=500, detail="Upload failed")

@app.get("/download/{file_id}")
@limiter.limit("20/minute")
async def download_file(request: Request, file_id: str, background_tasks: BackgroundTasks):
    normal_path = os.path.join(UPLOAD_DIR, f"{file_id}.bin")
    burn_path = os.path.join(UPLOAD_DIR, f"{file_id}.burn.bin")
    
    target_path = burn_path if os.path.exists(burn_path) else normal_path

    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    def delete_burn_file(path: str):
        time.sleep(2) 
        try:
            if os.path.exists(path) and ".burn.bin" in path:
                os.remove(path)
        except Exception as e:
            pass

    if target_path == burn_path:
        background_tasks.add_task(delete_burn_file, target_path)

    return FileResponse(
        path=target_path, 
        media_type="application/octet-stream", 
        filename="encrypted.bin"
    )

load_dotenv()
