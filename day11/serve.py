import os
import sys
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from day10.persistent_api import app

CHAT_HTML = os.path.join(os.path.dirname(__file__), 'chat.html')

@app.get('/')
def serve_chat_ui():
    return FileResponse(CHAT_HTML)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('day11.serve:app', host='0.0.0.0', port=8000, reload=False)
