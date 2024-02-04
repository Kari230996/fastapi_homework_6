from typing import Dict, Union
from fastapi import FastAPI, HTTPException, Depends, status

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from databases import Database
from pydantic import BaseModel
from datetime import datetime

# Подключение к базе данных SQLite
DATABASE_URL = "sqlite:///./test.db"
database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Модель таблицы "Пользователи"
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

# Модель таблицы "Товары"
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)

# Модель таблицы "Заказы"
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    order_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Pydantic модели для валидации данных
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

class ItemCreate(BaseModel):
    name: str
    description: str
    price: float

class OrderCreate(BaseModel):
    user_id: int
    item_id: int

class ItemRead(BaseModel):
    id: int
    name: str
    description: str
    price: float

class OrderResponse(BaseModel):
    id: int
    user_id: int
    item_id: int
    order_date: datetime
    status: str


class OrderRead(BaseModel):
    id: int
    user_id: int
    item_id: int
    order_date: datetime
    status: str

# CRUD операции для пользователей
@app.post("/users/", response_model=None)
async def create_user(user: UserCreate):
    try:
        query = User.__table__.insert().values(**user.dict())
        user_id = await database.execute(query)
        return {**user.dict(), "id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/", response_model=Dict[str, Union[int, str, float, bool, None]])
async def read_user(user_id: int):
    try:
        query = User.__table__.select().where(User.id == user_id)
        user = await database.fetch_one(query)
        if user:
            return dict(user)
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        print(f"Exception in read_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@app.put("/users/{user_id}/", response_model=UserCreate)
async def update_user(user_id: int, user: UserCreate):
    try:
        query = User.__table__.update().where(User.id == user_id).values(**user.dict())
        await database.execute(query)
        return {**user.dict(), "id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{user_id}/", response_model=dict)
async def delete_user(user_id: int):
    try:
        query = User.__table__.delete().where(User.id == user_id)
        await database.execute(query)
        return {"message": "User deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# CRUD операции для товаров
@app.post("/items/", response_model=ItemRead)
async def create_item(item: ItemCreate):
    try:
        query = Item.__table__.insert().values(**item.dict())
        item_id = await database.execute(query)
        return {**item.dict(), "id": item_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/items/{item_id}/", response_model=ItemRead)
async def read_item(item_id: int):
    try:
        query = Item.__table__.select().where(Item.id == item_id)
        item = await database.fetch_one(query)
        if item:
            return item
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/items/{item_id}/", response_model=ItemRead)
async def update_item(item_id: int, item: ItemCreate):
    try:
        query = Item.__table__.update().where(Item.id == item_id).values(**item.dict())
        await database.execute(query)
        return {**item.dict(), "id": item_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/items/{item_id}/", response_model=dict)
async def delete_item(item_id: int):
    try:
       
        existing_item = await database.fetch_one(Item.__table__.select().where(Item.id == item_id))
        if not existing_item:
            raise HTTPException(status_code=404, detail="Item not found")

        query = Item.__table__.delete().where(Item.id == item_id)
        await database.execute(query)

        return {"message": "Item deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# CRUD операции для заказов
@app.post("/orders/", response_model=OrderResponse)
async def create_order(order: OrderCreate):
    try:
        query = Order.__table__.insert().values(**order.dict(), order_date=datetime.utcnow(), status="pending")
        order_id = await database.execute(query)
        return {"id": order_id, **order.dict(), "order_date": datetime.utcnow(), "status": "pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders/{order_id}/", response_model=OrderRead)
async def read_order(order_id: int):
    try:
        query = Order.__table__.select().where(Order.id == order_id)
        order = await database.fetch_one(query)

        if order:
            return order
        else:
            raise HTTPException(status_code=404, detail="Order not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/orders/{order_id}/", response_model=OrderResponse)
async def update_order(order_id: int, status: str = "pending"):
    try:
        # Check if the order exists
        existing_order = await database.fetch_one(Order.__table__.select().where(Order.id == order_id))
        if not existing_order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Update the order status
        query = text(f"UPDATE orders SET status='{status}' WHERE id={order_id}")
        await database.execute(query)

        # Return the updated order details
        updated_order = {**existing_order, "status": status}
        return updated_order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/orders/{order_id}/", response_model=dict)
async def delete_order(order_id: int):
    try:
        # Check if the order exists
        existing_order = await database.fetch_one(Order.__table__.select().where(Order.id == order_id))
        if not existing_order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Delete the order
        query = Order.__table__.delete().where(Order.id == order_id)
        await database.execute(query)

        return {"message": "Order deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
