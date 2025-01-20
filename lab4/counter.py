import pymongo
import threading
from pymongo import MongoClient, WriteConcern
from time import time

MONGO_URI = "mongodb://mongo-primary:27017,mongo-secondary-1:27017,mongo-secondary-2:27017/?replicaSet=rs0&w=majority"
DB_NAME = "likes"
COLLECTION_NAME = "likes"
COUNTER_ID = "likeCounter3"

INCREMENTS_PER_CLIENT = 10000
CLIENTS_COUNT = 10


def increment_likes(client_id, increments):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    print(f"Client {client_id} starting...")
    for _ in range(increments):
        collection.find_one_and_update(
            {"_id": COUNTER_ID},
            {"$inc": {"count": 1}},
        )
    print(f"Client {client_id} finished.")


def run_clients():
    threads = []
    start_time = time()

    for i in range(CLIENTS_COUNT):
        thread = threading.Thread(
            target=increment_likes, args=(i + 1, INCREMENTS_PER_CLIENT))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time = time()
    print(f"Total time taken: {end_time - start_time} seconds")

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    result = collection.find_one({"_id": COUNTER_ID})
    print(f"Final like count: {result['count']}")


if __name__ == "__main__":
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    print(client.write_concern)
    collection.update_one(
        {"_id": COUNTER_ID},
        {"$setOnInsert": {"count": 0}},
        upsert=True
    )

    run_clients()
