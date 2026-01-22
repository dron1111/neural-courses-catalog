from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Каталог курсов по нейросетям")

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Каталог курсов по нейросетям"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
