from fastapi import FastAPI

app = FastAPI(title="Task Processor API", version="1.0.0")

@app.get("/")
def read_root():
    return {"message": "Task Processor API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "worker"}