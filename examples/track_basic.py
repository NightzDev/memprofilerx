from memprofilerx.tracker import track_memory
import time

@track_memory(interval=1)
def allocate_memory():
    data = [i for i in range(10_000_000)]
    time.sleep(2)
    return "Complete!"

if __name__ == "__main__":
    result = allocate_memory()
    print("Result:", result["result"])
    print("Memory usage:", result["memory_usage"])
