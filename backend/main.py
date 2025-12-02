from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.models import StartChatRequest, ChatMessageRequest, ChatResponse
from app.assistant import create_thread, add_message_to_thread, run_assistant
from app.tools import MOCK_PRODUCTS
from typing import Optional
import os

app = FastAPI(title="NeoBI Backend")

# Frontend build klasörü (production'da React build dosyaları burada)
FRONTEND_BUILD_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/dist"))

# CORS Configuration
# Production'da aynı origin olacağı için CORS gereksiz olabilir,
# ama development ve test için açık bırakıyoruz
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:6000",
    "https://neobicb.neocortexbe.com",
    "https://neobicb-test.neocortexbe.com",
    "https://exp.app.neoone.com.tr",  # NeoSales Web - Production
    "https://*.app.neoone.com.tr",    # NeoSales Web - Wildcard
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/products")
async def get_products():
    """
    Returns the current state of products (including live discounts).
    """
    return MOCK_PRODUCTS

@app.post("/api/chat/start")
async def start_chat(x_neoone_token: Optional[str] = Header(None)):
    """
    Starts a new chat session (thread).
    x_neoone_token: NeoOne kullanıcı token'ı (embedded modda gönderilir)
    """
    try:
        # Token varsa ileride kullanılabilir
        if x_neoone_token:
            print(f"DEBUG: NeoOne token received (length: {len(x_neoone_token)})")
        thread = create_thread()
        return {"thread_id": thread.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/message", response_model=ChatResponse)
async def send_message(request: ChatMessageRequest, x_neoone_token: Optional[str] = Header(None)):
    """
    Sends a message to the assistant and gets a response.
    x_neoone_token: NeoOne kullanıcı token'ı (embedded modda gönderilir)
    """
    try:
        # Token varsa NeoOne API isteklerinde kullanılabilir
        if x_neoone_token:
            print(f"DEBUG: Processing message with NeoOne token")
            # TODO: Token'ı api_client'a geçir
        
        add_message_to_thread(request.thread_id, request.message)
        response_text = run_assistant(request.thread_id)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PRODUCTION: React Frontend Static Serving
# ============================================

# Frontend build varsa static dosyaları mount et
if os.path.exists(FRONTEND_BUILD_PATH):
    # Assets klasörünü mount et (JS, CSS, images)
    assets_path = os.path.join(FRONTEND_BUILD_PATH, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    
    # Embed script için
    @app.get("/embed.js")
    async def embed_script():
        embed_path = os.path.join(FRONTEND_BUILD_PATH, "embed.js")
        if os.path.exists(embed_path):
            return FileResponse(embed_path, media_type="application/javascript")
        raise HTTPException(status_code=404)
    
    # Diğer static dosyalar için (favicon, manifest vs.)
    @app.get("/favicon.ico")
    async def favicon():
        favicon_path = os.path.join(FRONTEND_BUILD_PATH, "favicon.ico")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path)
        raise HTTPException(status_code=404)
    
    @app.get("/neobi-icon.png")
    async def neobi_icon():
        icon_path = os.path.join(FRONTEND_BUILD_PATH, "neobi-icon.png")
        if os.path.exists(icon_path):
            return FileResponse(icon_path)
        raise HTTPException(status_code=404)
    
    # Root path - index.html döndür
    @app.get("/")
    async def serve_root():
        index_path = os.path.join(FRONTEND_BUILD_PATH, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "NeoBI API is running. Frontend not found - run 'npm run build' in frontend folder."}
    
    # SPA Catch-all Route: API dışındaki tüm istekleri React'a yönlendir
    # Bu en sonda olmalı çünkü tüm path'leri yakalar
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """
        React SPA için catch-all route.
        API endpoint'leri zaten yukarıda tanımlı, onlar öncelikli.
        Diğer tüm GET istekleri index.html'e yönlendirilir.
        """
        # API isteklerini 404 döndür (zaten handle edilmiş olmalı)
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        index_path = os.path.join(FRONTEND_BUILD_PATH, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend not built")
else:
    @app.get("/")
    async def root():
        return {"message": "NeoBI API is running. Frontend not built yet - run 'npm run build' in frontend folder."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
