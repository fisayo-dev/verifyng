from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .result import router as result_router
from .payments import router as payments_router
from .verifications import router as verifications_router

app = FastAPI(title="VerifyNG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(result_router)
app.include_router(payments_router)
app.include_router(verifications_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "VerifyNG",
    }
