import json
import os

class Preferences:
    def __init__(self):

        self.path_tool = ""
        self.environment_name = ""

    def update_values(self, environment_name, path_tool):

        self.environment_name = environment_name
        self.path_tool = path_tool

    def save(self, archivo="userPreferences.json"):

        with open(archivo, "w") as archivo:
            json.dump(self.__dict__, archivo)

    def load(self, archivo="userPreferences.json"):

        if os.path.exists(archivo):
            with open(archivo, "r") as archivo:
                datos = json.load(archivo)
                self.__dict__.update(datos)
