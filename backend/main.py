from fastapi import FastAPI

app = FastAPI(title="File Processing API", version="1.0.0")

@app.get("/")
def read_root():
    return {"message": "File Processing API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "backend"}