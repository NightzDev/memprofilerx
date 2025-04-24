from memprofilerx.tracker import track_memory
import time

@track_memory(interval=1, analyze_gc=True)
def leak_simulator():
    cache = [{"a": i, "b": str(i)} for i in range(100_000)]
    time.sleep(3)

if __name__ == "__main__":
    result = leak_simulator()
    print("\n🔍 Live objects:")
    for key, value in result["live_objects"].items():
        print(f"{key}: {value}")
