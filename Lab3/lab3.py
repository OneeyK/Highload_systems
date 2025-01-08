import time
import threading
from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
username = "neo4j"
password = "12345678"
driver = GraphDatabase.driver(uri, auth=(username, password))


counter_lock = threading.Lock()

shared_counter = 0


def increment_likes_query(transaction, item_id, count):
    transaction.run("""
        MATCH (i:Item)
        WHERE i.item_id = $item_id
        SET i.likes = COALESCE(i.likes, 0) + $count
    """, item_id=item_id, count=count)


def increment_likes(item_id):
    global shared_counter

    for _ in range(10000):
        with counter_lock:
            shared_counter += 1

        with driver.session() as session:
            session.write_transaction(increment_likes_query, item_id, 1)


def run_increment_threads():
    threads = []
    num_threads = 10

    for _ in range(num_threads):
        thread = threading.Thread(
            target=increment_likes, args=(1,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


start_time = time.time()

run_increment_threads()

end_time = time.time()

print(f"Execution time: {end_time - start_time} seconds")
print(f"Total likes incremented: {shared_counter}")
