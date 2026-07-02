from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Training Plan Generator API is running"}
