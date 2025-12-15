import sys
import os

# 添加用户site-packages目录到sys.path
user_site_packages = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Python', 'Python38', 'site-packages')
if user_site_packages not in sys.path:
    sys.path.append(user_site_packages)

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uuid
import shutil
import random
import string
from datetime import datetime, timedelta
import asyncio
import os



FlashDrop = FastAPI()



# 配置
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
FILE_EXPIRY_TIME = timedelta(minutes=10)

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 静态文件服务，默认首页为index.html
FlashDrop.mount("/static", StaticFiles(directory="static", html=True), name="static")


def generate_code():
    """生成一个不重复的4位数字代码"""
    while True:
        code = str(random.randint(1000, 9999))
        # 检查本地文件系统是否已经有这个码了
        if not os.path.exists(os.path.join(UPLOAD_DIR, code)):
            return code

# 根路径重定向到静态文件
@FlashDrop.get("/")
def read_root():
    return FileResponse("static/index.html")

# 文件上传API
@FlashDrop.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 检查文件大小
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 50MB allowed.")
    
    # 生成4位随机码作为文件名
    code = generate_code()
    
    # 获取原始文件扩展名
    file_extension = os.path.splitext(file.filename)[1]
    
    # 构建带扩展名的文件名
    file_name_with_ext = f"{code}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name_with_ext)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 创建元数据文件存储原始文件名
    metadata_file = os.path.join(UPLOAD_DIR, f"{code}.meta")
    with open(metadata_file, "w") as f:
        f.write(file.filename)
    
    # 异步清理过期文件和元数据
    asyncio.create_task(cleanup_file(file_path))
    asyncio.create_task(cleanup_file(metadata_file))    
    
    return {"code": code, "filename": file.filename, "message": "上传成功，请在10分钟内使用"}

# 文件下载API
@FlashDrop.get("/download/{code}")
def download_file(code: str):
    # 查找匹配的文件（带任意扩展名）
    matching_files = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(code) and not f.endswith('.meta')]
    
    if not matching_files:
        raise HTTPException(status_code=404, detail="代码无效或文件已过期.")
    
    file_path = os.path.join(UPLOAD_DIR, matching_files[0])
    
    # 尝试读取原始文件名
    metadata_file = os.path.join(UPLOAD_DIR, f"{code}.meta")
    original_filename = None
    
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            original_filename = f.read().strip()
    
    # 如果没有元数据文件，使用匹配到的文件名
    if not original_filename:
        original_filename = matching_files[0]
    
    # 获取文件扩展名并设置正确的媒体类型
    file_extension = os.path.splitext(original_filename)[1].lower()
    
    # 简单的媒体类型映射
    media_types = {
        '.txt': 'text/plain',
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.mp4': 'video/mp4',
        '.mp3': 'audio/mpeg',
        '.zip': 'application/zip',
        '.rar': 'application/x-rar-compressed',
        '.7z': 'application/x-7z-compressed'
    }
    
    media_type = media_types.get(file_extension, "application/octet-stream")
    
    # 准备要删除的文件列表
    files_to_delete = [file_path]
    if os.path.exists(metadata_file):
        files_to_delete.append(metadata_file)
    
    # 返回文件并在下载后删除所有相关文件
    return FileResponse(
        path=file_path,
        filename=original_filename,
        media_type=media_type,
        background=CleanupFileBackground(files_to_delete)
    )

# 后台任务：下载后清理文件
class CleanupFileBackground:
    def __init__(self, files_to_delete):
        # 可以接受单个文件路径或文件路径列表
        self.files_to_delete = files_to_delete if isinstance(files_to_delete, list) else [files_to_delete]
    
    async def __call__(self):
        for file_path in self.files_to_delete:
            if os.path.exists(file_path):
                os.remove(file_path)

# 异步任务：过期后清理文件
async def cleanup_file(file_path: str):
    await asyncio.sleep(FILE_EXPIRY_TIME.total_seconds())
    
    # 清理主文件
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # 如果是带扩展名的主文件，尝试清理对应的元数据文件
    code = os.path.splitext(os.path.basename(file_path))[0]
    metadata_file = os.path.join(UPLOAD_DIR, f"{code}.meta")
    if os.path.exists(metadata_file):
        os.remove(metadata_file)
    
    # 如果是元数据文件，尝试清理对应的主文件
    elif file_path.endswith('.meta'):
        # 查找所有以该code开头的非.meta文件
        for f in os.listdir(UPLOAD_DIR):
            if f.startswith(code) and not f.endswith('.meta'):
                main_file = os.path.join(UPLOAD_DIR, f)
                if os.path.exists(main_file):
                    os.remove(main_file)

# 启动时清理所有过期文件
def cleanup_expired_files():
    now = datetime.now()
    processed_codes = set()
    
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        # 检查文件是否过期
        if now - file_mtime > FILE_EXPIRY_TIME:
            # 获取文件的code部分
            code = os.path.splitext(filename)[0]
            
            # 如果这个code还没有处理过
            if code not in processed_codes:
                processed_codes.add(code)
                
                # 清理所有与该code相关的文件（主文件和元数据文件）
                for f in os.listdir(UPLOAD_DIR):
                    if f.startswith(code):
                        expired_file = os.path.join(UPLOAD_DIR, f)
                        if os.path.exists(expired_file):
                            os.remove(expired_file)

# 初始化清理
cleanup_expired_files()

# 直接运行时启动服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:FlashDrop", host="127.0.0.1", port=8080, reload=False)