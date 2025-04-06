import tkinter as tk

from ManagePreferences import Preferences
from Interfaces import MainApp

def main():
    # Crear ventana principal
    root = tk.Tk()
    
    # Cargar preferencias antes de crear la aplicación
    preferences = Preferences()
    preferences.load()
    
    # Pasar las preferencias a MainApp
    app = MainApp(root, preferences)
    
    root.mainloop()

if __name__ == "__main__":
    main()