import random
import statistics
import time
import uuid

from qdrant_client import models

from app.db.qdrant_client import client

DIM = 1536


def make_points(n):
    return [
        models.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"bench-{i}")),
            vector=[random.random() for _ in range(DIM)],
            payload={"source": f"doc-{i % 50}", "year": 2020 + i % 7},
        )
        for i in range(n)
    ]


def fresh_collection(name="bench_tmp"):
    if client.collection_exists(name):
        client.delete_collection(name)
    client.create_collection(name, vectors_config=models.VectorParams(size=DIM, distance=models.Distance.COSINE))


def bench(points, batch_size, parallel, repeats=3):
    times = []
    for _ in range(repeats):
        fresh_collection()
        t0 = time.perf_counter()
        client.upload_points("bench_tmp", points, batch_size=batch_size, parallel=parallel, wait=True)
        times.append(time.perf_counter() - t0)
    med = statistics.median(times)
    print(f"batch={batch_size} parallel={parallel}: median {med:.1f}s, {len(points) / med:.0f} points/s")


if __name__ == "__main__":
    t0 = time.perf_counter()
    pts = make_points(5000)
    print(f"генерация точек: {time.perf_counter() - t0:.1f}s")
    for bs, par in [(256, 1), (256, 2), (256, 4)]:
        bench(pts, bs, par)
    client.delete_collection("bench_tmp")
