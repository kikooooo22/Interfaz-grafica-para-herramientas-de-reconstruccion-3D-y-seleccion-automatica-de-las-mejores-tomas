import tkinter as tk

from Interfaces import MainApp

def main():

    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()