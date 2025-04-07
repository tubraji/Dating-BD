import json
import os

DATA_PATH = "data/users.json"

def load_users():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(DATA_PATH, 'w') as f:
        json.dump(users, f, indent=2)
