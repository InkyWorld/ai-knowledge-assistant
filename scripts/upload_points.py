import random
import statistics
import time
import uuid

from qdrant_client import models

from app.core.clients import get_qdrant

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
    qdrant = get_qdrant()
    if qdrant.collection_exists(name):
        qdrant.delete_collection(name)
    qdrant.create_collection(name, vectors_config=models.VectorParams(size=DIM, distance=models.Distance.COSINE))


def bench(points, batch_size, parallel, repeats=3):
    qdrant = get_qdrant()
    times = []
    for _ in range(repeats):
        fresh_collection()
        t0 = time.perf_counter()
        qdrant.upload_points("bench_tmp", points, batch_size=batch_size, parallel=parallel, wait=True)
        times.append(time.perf_counter() - t0)
    med = statistics.median(times)
    print(f"batch={batch_size} parallel={parallel}: median {med:.1f}s, {len(points) / med:.0f} points/s")


if __name__ == "__main__":
    t0 = time.perf_counter()
    pts = make_points(5000)
    print(f"point generation: {time.perf_counter() - t0:.1f}s")
    for bs, par in [(1024, 1), (256, 1), (512, 1), (256, 4)]:
        bench(pts, bs, par)
    get_qdrant().delete_collection("bench_tmp")

# first run:
# point generation: 1.7s
# batch=1024 parallel=1: median 5.5s, 914 points/s
# batch=256 parallel=1: median 5.3s, 936 points/s
# batch=64 parallel=1: median 6.7s, 747 points/s
# batch=256 parallel=4: median 7.4s, 674 points/s

# second run:
# point generation: 1.7s
# batch=1024 parallel=1: median 5.1s, 982 points/s
# batch=256 parallel=1: median 5.3s, 949 points/s
# batch=512 parallel=1: median 4.9s, 1017 points/s
# batch=256 parallel=4: median 7.2s, 698 points/s