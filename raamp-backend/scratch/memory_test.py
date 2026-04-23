
import base64
import io
import os
import psutil
import time

def old_encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def new_encode_image(image_path: str) -> str:
    output = io.StringIO()
    with open(image_path, "rb") as f:
        for chunk in iter(lambda: f.read(3072), b""):
            output.write(base64.b64encode(chunk).decode('utf-8'))
    return output.getvalue()

def measure_peak_memory(func, *args):
    process = psutil.Process(os.getpid())
    start_mem = process.memory_info().rss
    peak_mem = start_mem
    
    # We use a thread-like approach or just simple tracking
    result = func(*args)
    peak_mem = max(peak_mem, process.memory_info().rss)
    
    end_mem = process.memory_info().rss
    return result, peak_mem - start_mem

# Create a 10MB dummy file
test_file = "test_image.bin"
with open(test_file, "wb") as f:
    f.write(os.urandom(10 * 1024 * 1024))

print(f"File size: {os.path.getsize(test_file) / (1024*1024):.2f} MB")

import threading

def run_concurrent(func, count):
    threads = []
    for i in range(count):
        t = threading.Thread(target=func, args=(test_file,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

print("\n--- CONCURRENT TEST (5 images) ---")
process = psutil.Process(os.getpid())
base_mem = process.memory_info().rss

print("Testing Old Method (Concurrent)...")
run_concurrent(old_encode_image, 5)
peak_old = process.memory_info().rss - base_mem
print(f"Old peak: {peak_old / (1024*1024):.2f} MB")

# GC to be fair
import gc
gc.collect()
base_mem = process.memory_info().rss

print("Testing New Method (Concurrent)...")
run_concurrent(new_encode_image, 5)
peak_new = process.memory_info().rss - base_mem
print(f"New peak: {peak_new / (1024*1024):.2f} MB")

os.remove(test_file)
