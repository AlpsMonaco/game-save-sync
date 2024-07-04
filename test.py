import os


for i in range(0, 10):
    with open(f"base_library/{i}.txt", "w") as fd:
        for j in range(0, i % 5):
            fd.write(str(i + j))
