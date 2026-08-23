import uvicorn
from dotenv import load_dotenv

from app import create_app

app = create_app()

if __name__ == "__main__":
    load_dotenv(".env")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True
    )
else:
    application = app