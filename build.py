import subprocess
import sys

commands = [
    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
    [sys.executable, "manage.py", "collectstatic", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]

for cmd in commands:
    print(f">>> Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}")
        sys.exit(result.returncode)

print("Build completed successfully.")
