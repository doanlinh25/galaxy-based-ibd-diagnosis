import os
import json

def load_state_running(n = 0):
    if n == 0:
        STATE_FILE = r"C:\Users\User\ppnckh\running_jobs\shared_state\running_wf0.json"
    else:
        STATE_FILE = r"C:\Users\User\ppnckh\running_jobs\shared_state\running_wf1.json"
    state_dir = os.path.dirname(STATE_FILE)
    if state_dir:
        os.makedirs(state_dir, exist_ok=True)

    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            json.dump({"running_jobs": []}, f, indent=4)
        return []

    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            return state.get("running_jobs", [])
    except json.JSONDecodeError:
        with open(STATE_FILE, "w") as f:
            json.dump({"running_jobs": []}, f, indent=4)
        return []

def load_state_delete(n = 0):
    if n == 0:
        STATE_FILE = r"C:\Users\User\ppnckh\running_jobs\shared_state\delete_wf0.json"
    else:
        STATE_FILE = r"C:\Users\User\ppnckh\running_jobs\shared_state\delete_wf1.json"
    state_dir = os.path.dirname(STATE_FILE)
    if state_dir:
        os.makedirs(state_dir, exist_ok=True)

    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            json.dump({"running_jobs": []}, f, indent=4)
        return []

    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            return state.get("running_jobs", [])
    except json.JSONDecodeError:
        with open(STATE_FILE, "w") as f:
            json.dump({"running_jobs": []}, f, indent=4)
        return []

def save_state_running(running_jobs, n = 0):
    if n == 0:
        STATE_FILE = r"C:\Users\User\ppnckh\running_jobs\shared_state\running_wf0.json"
    else:
        STATE_FILE = r"C:\Users\User\ppnckh\running_jobs\shared_state\running_wf1.json"
    state_dir = os.path.dirname(STATE_FILE)
    if state_dir:
        os.makedirs(state_dir, exist_ok=True)

    with open(STATE_FILE, "w") as f:
        json.dump({"running_jobs": running_jobs}, f, indent=2)

def save_state_delete(running_jobs, n = 0):
    if n == 0:
        STATE_FILE = r"C:\Users\User\ppnckh\running_jobs\shared_state\delete_wf0.json"
    else:
        STATE_FILE = r"C:\Users\User\ppnckh\running_jobs\shared_state\delete_wf1.json"
    state_dir = os.path.dirname(STATE_FILE)
    if state_dir:
        os.makedirs(state_dir, exist_ok=True)

    with open(STATE_FILE, "w") as f:
        json.dump({"running_jobs": running_jobs}, f, indent=2)

def save_failed_srr(srr, n = 0):
    if n == 0:
        ERR_FILE = r"C:\Users\User\ppnckh\err_srrs\failed_srrs_wf0.json"
    else:
        ERR_FILE = r"C:\Users\User\ppnckh\err_srrs\failed_srrs_wf1.json"
    os.makedirs(os.path.dirname(ERR_FILE), exist_ok=True)

    if os.path.exists(ERR_FILE):
        with open(ERR_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    if srr not in data:
        data.append(srr)

    with open(ERR_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_failed_srr(n = 0):
    if n == 0:
        ERR_FILE = r"C:\Users\User\ppnckh\err_srrs\failed_srrs_wf0.json"
    else:
        ERR_FILE = r"C:\Users\User\ppnckh\err_srrs\failed_srrs_wf1.json"
    os.makedirs(os.path.dirname(ERR_FILE), exist_ok=True)

    if os.path.exists(ERR_FILE):
        with open(ERR_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []
    return data

def clear_failed_srr(n=0):
    if n == 0:
        ERR_FILE = r"C:\Users\User\ppnckh\err_srrs\failed_srrs_wf0.json"
    else:
        ERR_FILE = r"C:\Users\User\ppnckh\err_srrs\failed_srrs_wf1.json"
    if os.path.exists(ERR_FILE):
        os.remove(ERR_FILE)