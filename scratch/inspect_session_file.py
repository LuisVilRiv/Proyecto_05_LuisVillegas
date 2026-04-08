import flet as ft
from pathlib import Path

def main(page: ft.Page):
    res = f"TYPE: {type(page.session)}\nDIR: {dir(page.session)}"
    Path("scratch/session_info.txt").write_text(res)
    # No need to close, the killer thread will do it

if __name__ == "__main__":
    import threading
    import time
    import os
    def killer():
        time.sleep(3)
        os._exit(0)
    threading.Thread(target=killer, daemon=True).start()
    ft.run(main)
