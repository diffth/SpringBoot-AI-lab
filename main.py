from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = 0.1

items = {100: Item(name="pen", price=12.5, tax=0.015),
        200: Item(name="book", price=12.5)}

@app.get("/")
async def index():
    return {"message": "Hello FastAPI!"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.post("/items/")
async def create_item(item: Item):
    item_id = max(items.keys()) + 100
    items[item_id] = item
    return {"item_id": item_id, **item.model_dump()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)