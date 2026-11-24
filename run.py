"""Khởi động TradeFlow:  python run.py"""
import threading
import webbrowser

from tradeflow.app import create_app
from tradeflow.core.config import Settings, load_dotenv


def main() -> None:
    load_dotenv()
    settings = Settings.from_env()
    app = create_app(settings)
    url = f"http://{settings.host}:{settings.port}"
    print(f"\nTradeFlow đang chạy tại {url}\nNhấn Ctrl+C để dừng.\n")
    if settings.host in ("127.0.0.1", "localhost") and not settings.debug:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    app.run(host=settings.host, port=settings.port, debug=settings.debug)


if __name__ == "__main__":
    main()
