try:
    import fastapi
    print("FastAPI installed successfully!")
    import uvicorn
    print("Uvicorn installed successfully!")
    import python_multipart
    print("Python-multipart installed successfully!")
    import aiofiles
    print("Aiofiles installed successfully!")
except ImportError as e:
    print(f"Import error: {e}")