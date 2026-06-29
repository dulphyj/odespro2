import os
import shutil
import subprocess
import sys


def build():
    dist_dir = os.path.join(os.path.dirname(__file__), "dist")
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "DocApp-Desktop",
        "--add-data", f"app{os.pathsep}app",
        "--add-data", f"desktop{os.pathsep}desktop",
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "--hidden-import", "sqlalchemy",
        "--hidden-import", "pydantic",
        "--hidden-import", "PIL",
        "--hidden-import", "numpy",
        "--hidden-import", "easyocr",
        "desktop_app.py",
    ]

    print("Ejecutando PyInstaller...")
    subprocess.check_call(cmd, cwd=os.path.dirname(__file__))
    print(f"Build completo: {os.path.join(dist_dir, 'DocApp-Desktop.exe')}")


if __name__ == "__main__":
    build()
