import threading

from modules.client import Client
from modules.client.MainMenu import MainMenu
from modules.client.GameMenu import GameMenu
from modules.data.loader import Loader
from modules.data import data

from line_profiler import profile
import asyncio

@profile
def main():
    loader = Loader()
    loader.load()

    client = Client()

    data.client = client
    data.loop = start_async_loop()

    client.display(MainMenu())
    client.run()

def start_async_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    return loop

if __name__ == '__main__':
    main()