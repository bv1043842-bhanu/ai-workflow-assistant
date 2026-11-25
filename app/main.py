from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "AI Workflow Assistant backend is running",
    }
