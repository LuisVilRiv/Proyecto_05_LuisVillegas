import flet as ft
def main(page: ft.Page):
    print("SESSION TYPE:", type(page.session))
    print("SESSION DIR:", dir(page.session))
    page.window.close() # Close immediately or just exit

if __name__ == "__main__":
    # We use a very short timeout or just exit after print
    import threading
    import time
    def killer():
        time.sleep(2)
        import os
        os._exit(0)
    threading.Thread(target=killer, daemon=True).start()
    ft.run(main)
