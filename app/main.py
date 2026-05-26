from fastapi import FastAPI
from app.core.settings import settings

app = FastAPI(
    title="Mundo Invest Backend",
    version="0.1.0",
    debug=settings.DEBUG,
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
