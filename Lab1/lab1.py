import hazelcast
import threading
import time


client = hazelcast.HazelcastClient(cluster_name='my-cluster')
distributed_map = client.get_map("my-distributing-map").blocking()


def task3():
    global counter
    lock = threading.Lock()
    for i in range(10000):
        with lock:
            counter += 1
            distributed_map.put('t3', counter)


def task4():
    distributed_map.put("t4", 0)
    for i in range(10000):
        counter = distributed_map.get("t4") + 1
        distributed_map.put("t4", counter)


def task5():
    if not distributed_map.contains_key("t5"):
        distributed_map.put("t5", 0)
    for i in range(10000):
        distributed_map.lock("t5")
        try:
            value = distributed_map.get("t5") + 1
            distributed_map.put("t5", value)
        finally:
            distributed_map.unlock("t5")


def task6():
    if not distributed_map.contains_key("t6"):
        distributed_map.put("t6", 0)
    for i in range(10000):
        while True:
            oldValue = distributed_map.get("t6")
            newValue = oldValue + 1
            if distributed_map.replace_if_same("t6", oldValue, newValue):
                break


def task7():
    atomic_long = client.cp_subsystem.get_atomic_long('t7').blocking()
    for i in range(10000):
        atomic_long.increment_and_get()


counter = 0
start = time.time()
threads = []
for _ in range(10):
    thread = threading.Thread(target=task7)
    threads.append(thread)

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()
print(f"Time taken = {time.time() - start}")
print(f'Final counter = {distributed_map.get("t7")}')
