import flet as ft
from pathlib import Path

def main(page: ft.Page):
    res = f"STORE TYPE: {type(page.session.store)}\nSTORE DIR: {dir(page.session.store)}"
    Path("scratch/session_store_info.txt").write_text(res)

if __name__ == "__main__":
    import threading
    import time
    import os
    def killer():
        time.sleep(3)
        os._exit(0)
    threading.Thread(target=killer, daemon=True).start()
    ft.run(main)
