import uvicorn
from fastapi import FastAPI
from app.api import router

app = FastAPI(
    title="CTUIL PDF Downloader API",
    version="1.0.0",
)

# Include the routes
app.include_router(router, prefix="/api/v1")

@app.get("/", tags=["Health"])
def root():
    return {"message": "CTUIL PDF Downloader API is running. Visit /docs for API documentation."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
