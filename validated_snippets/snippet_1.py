from fastapi import FastAPI

app = FastAPI()

@app.get="/hello"
def read_root():
    print("Received request to /hello")
    result = {"message": "Hello, World!"}
    print("Returning result:", result)
    return result

if __name__ == "__main__":
    import uvicorn
    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
    print("Server started on port 8000")
