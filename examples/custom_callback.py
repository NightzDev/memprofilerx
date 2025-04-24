from memprofilerx.tracker import track_memory
import time

def log_to_console(ts, mem):
    print(f"[callback] {ts:.2f}s → {mem:.2f} MB")

@track_memory(interval=1, callback=log_to_console)
def allocate_and_wait():
    x = [i for i in range(5_000_000)]
    time.sleep(3)

if __name__ == "__main__":
    allocate_and_wait()
