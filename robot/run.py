import threading
from app import create_app
from worker import run_worker

app = create_app()

if __name__ == "__main__":
    # Start Email Worker Thread
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()

    # Start Flask Server
    print("🔥 Backend System is Online")
    app.run(host="0.0.0.0", port=5000, debug=False)