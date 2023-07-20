#uvicorn main:app --reload
# import requests
# import json
import redis
from fastapi import FastAPI, WebSocket 
from database import SessionLocal
from models import Message



redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


# @app.get("/messages/{species}") 
# def read_fish(species: str):
#     cache = redis.get(species)
#     if cache: 
#         print('hit in cache')
#         return cache.decode()
#     else: 
#         print('miss in cache')
#         req = requests.get(f"https://swapi.dev/api/species/{species}/")
#         redis.set(species, req.text)
#         redis.expire(species, 100)
#         return {'req returned': req.json()} 

@app.websocket("/ws/{user}")
async def websocket_endpoint(user: str, websocket: WebSocket):
    await websocket.accept()

    # Connect to Redis
    redis_conn = await redis.pubsub()
    await redis_conn.subscribe("chat")

    # Create a database session
    db = SessionLocal()

    try:
        while True:
            # Receive messages from Redis
            data = await redis_conn.get_message(ignore_subscribe_messages=True)
            if data is not None:
                message = data["data"].decode()

                # Send message to WebSocket
                await websocket.send_text(message)

                # Save message to the database
                db_message = Message(content=message, sender=user)
                db.add(db_message)
                db.commit()

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close Redis connection and database session
        await redis_conn.close()
        db.close()

