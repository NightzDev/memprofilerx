from memprofilerx.tracker import global_tracker
import time

@global_tracker(interval=1, export_png="global_mem.png")
def run_app():
    data = [i for i in range(10_000_000)]
    time.sleep(4)

if __name__ == "__main__":
    run_app()
    print("✅ Graph exported as global_mem.png")
