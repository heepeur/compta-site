
from flask import Flask, render_template, request, jsonify
import json, os, requests
from datetime import datetime
import pytz

app = Flask(__name__)

DATA_FILE = "data.json"
MESSAGE_ID_FILE = "messageid.txt"
WEBHOOK_URL = "WEBHOOK_URL"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_webhook_message_id():
    if os.path.exists(MESSAGE_ID_FILE):
        with open(MESSAGE_ID_FILE, "r") as f:
            return f.read().strip()
    return None

def save_webhook_message_id(message_id):
    with open(MESSAGE_ID_FILE, "w") as f:
        f.write(message_id)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/entries", methods=["GET"])
def get_entries():
    return jsonify(load_data())

@app.route("/api/entries", methods=["POST"])
def add_entry():
    new_entry = request.json
    data = load_data()
    data.append(new_entry)
    save_data(data)
    return jsonify({"status": "success"})

@app.route("/api/entries/<int:index>", methods=["PUT"])
def edit_entry(index):
    updated_entry = request.json
    data = load_data()
    if 0 <= index < len(data):
        data[index] = updated_entry
        save_data(data)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route("/api/entries/<int:index>", methods=["DELETE"])
def delete_entry(index):
    data = load_data()
    if 0 <= index < len(data):
        data.pop(index)
        save_data(data)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
