from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analytics, auth, fleet, telemetry

app = FastAPI(title="Smart Vehicle Fleet Management API", version="1.0.0", openapi_url="/api/openapi.json", docs_url="/api/docs")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/api")
app.include_router(fleet.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(telemetry.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
