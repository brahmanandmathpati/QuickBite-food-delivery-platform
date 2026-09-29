import subprocess

for script in ["load_raw.py", "clean_staging.py", "build_marts.py"]:
    subprocess.run(["python", f"pipeline/{script}"], check=True)

print("Pipeline complete. Now run: pytest tests/ -v")