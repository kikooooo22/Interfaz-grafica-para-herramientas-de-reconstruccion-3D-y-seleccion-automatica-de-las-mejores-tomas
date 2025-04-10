import tkinter as tk

from Interfaces import MainApp

def main():

    root = tk.Tk()
    app = MainApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()