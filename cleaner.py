# -*- coding: utf-8 -*-
import os
import time
import logging

# 配置部分
UPLOAD_DIR = "uploads"          # 您的上传文件夹路径
MAX_AGE_SECONDS = 20 * 60       # 20分钟 (1200秒)
CHECK_INTERVAL = 60             # 每隔 60秒 检查一次

# 设置日志 (方便您查看清理记录)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cleaner.log"), # 日志写入文件
        logging.StreamHandler()             # 同时输出到控制台
    ]
)

def cleanup_files():
    """遍历文件夹并删除过期文件"""
    
    # 如果文件夹不存在，就跳过
    if not os.path.exists(UPLOAD_DIR):
        return

    now = time.time()
    
    # 获取文件夹内所有文件名
    try:
        files = os.listdir(UPLOAD_DIR)
    except Exception as e:
        logging.error("无法读取目录: {}".format(e))
        return

    for filename in files:
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # 确保是文件而不是子文件夹
        if not os.path.isfile(file_path):
            continue

        try:
            # 获取文件最后修改时间
            file_mtime = os.path.getmtime(file_path)
            
            # 计算文件年龄
            file_age = now - file_mtime
            
            # 如果文件年龄超过限制，执行删除
            if file_age > MAX_AGE_SECONDS:
                os.remove(file_path)
                logging.info("已删除过期文件: {} (存在时长: {}秒)".format(filename, int(file_age)))
                
        except Exception as e:
            # 即使某个文件删除失败，不要崩溃，继续处理下一个
            logging.error("删除文件失败 {}: {}".format(filename, e))

if __name__ == "__main__":
    logging.info("--- 清理服务已启动 ---")
    logging.info("监控目录: {}".format(UPLOAD_DIR))
    logging.info("过期时间: {} 秒".format(MAX_AGE_SECONDS))

    while True:
        cleanup_files()
        # 休息一下，避免占用过多 CPU
        time.sleep(CHECK_INTERVAL)