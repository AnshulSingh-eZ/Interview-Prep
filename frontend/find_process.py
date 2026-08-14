import os

src_dir = r"D:\Documents\Anshul\Interview_Prep\frontend\src"
for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith((".ts", ".tsx", ".js", ".jsx")):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                if "process.env" in content:
                    print(f"Found process.env in: {path}")
                if "process" in content and "process." in content:
                    print(f"Found process in: {path}")
