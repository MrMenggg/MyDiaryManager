import subprocess
import webbrowser
import time
import socket
import sys
import os


def wait_for_port(port, host='localhost', timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except Exception:
            time.sleep(0.5)
    return False

def run_streamlit(app_path, port=8501):
    url = f"http://localhost:{port}"
    proc = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.port", str(port),
        "--server.headless", "true"  # ✅ 防止自动打开浏览器
    ])
    if wait_for_port(port):
        webbrowser.open(url)
    else:
        print(f"Timeout: {port}端口未开启，无法打开浏览器。")
    proc.wait()

if __name__ == "__main__":
    app_file = os.path.join(os.path.dirname(__file__), "streamlit_app.py")
    run_streamlit(app_file)
