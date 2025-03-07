import json
import os

class Preferences:
    def __init__(self):

        self.preferences = {
            "path_tool": "",
            "environment_name": ""
        }

    def update(self, **kwargs):

        self.preferences.update(kwargs)

    def save(self, file="userPreferences.json"):

        with open(file, "w") as f:
            json.dump(self.preferences, f)

    def load(self, file="userPreferences.json"):

        if os.path.exists(file):
            with open(file, "r") as f:
                self.preferences.update(json.load(f))
