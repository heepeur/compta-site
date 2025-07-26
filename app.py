from flask import Flask, render_template, request, jsonify
import json
import os
import requests
from datetime import datetime
import pytz  # pip install pytz

app = Flask(__name__)

DATA_FILE = "data.json"
MESSAGE_ID_FILE = "C:/Users/Forza PC/Desktop/code/compta/messageid.txt"

WEBHOOK_URL = "https://discord.com/api/webhooks/1398323877528207443/zYe0wF8le79ilBk7x-T1NJZozLEZPHnR8KPUwtxyWW_nc5d3Lu8y0zvuraB4oXOZ4zbQ"  # <== Mets ton webhook ici

# Charger les données depuis le fichier JSON
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Sauvegarder les données dans le fichier JSON
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Lire l'ID du message Discord sauvegardé
def load_webhook_message_id():
    if os.path.exists(MESSAGE_ID_FILE):
        with open(MESSAGE_ID_FILE, "r") as f:
            return f.read().strip()
    return None

# Sauvegarder l'ID du message Discord
def save_webhook_message_id(message_id):
    with open(MESSAGE_ID_FILE, "w") as f:
        f.write(message_id)

# Format humain pour footer style "Today at 5:28 PM"
def human_date(dt, local_tz):
    today = datetime.now(local_tz).date()
    delta = (today - dt.date()).days
    if delta == 0:
        day_str = "Today"
    elif delta == 1:
        day_str = "Yesterday"
    else:
        day_str = dt.strftime("%d %b %Y")
    # %-I ne fonctionne pas sur Windows, on remplace par .lstrip('0') manuellement:
    hour = dt.strftime("%I").lstrip('0') or '0'
    minute = dt.strftime("%M")
    ampm = dt.strftime("%p")
    return f"{day_str} at {hour}:{minute} {ampm}"

# Construire l'embed Discord
def create_embed(entry, total_recettes, total_depenses):
    couleur = 0x28a745 if entry['type'] == 'Recette' else 0xdc3545

    local_tz = pytz.timezone("Europe/Paris")  # Change si besoin
    now_local = datetime.now(local_tz)

    footer_text = f"Compta Chirurgie - Mis à jour • {human_date(now_local, local_tz)}"
    now_iso = datetime.utcnow().isoformat()

    embed = {
        "embeds": [{
            "title": "💰 Nouvelle entrée comptable",
            "color": couleur,
            "fields": [
                {"name": "Date", "value": entry['date'], "inline": True},
                {"name": "Description", "value": entry['description'], "inline": True},
                {"name": "Montant", "value": f"{float(entry['montant']):.2f} €", "inline": True},
                {"name": "Type", "value": entry['type'], "inline": True},
                {"name": "Total Recettes", "value": f"{total_recettes:.2f} €", "inline": True},
                {"name": "Total Dépenses", "value": f"{total_depenses:.2f} €", "inline": True}
            ],
            "footer": {"text": footer_text},
            "timestamp": now_iso
        }]
    }
    return embed

# Envoyer un nouveau message webhook (à la création ou fallback)
def send_new_webhook(entry, total_recettes, total_depenses):
    embed = create_embed(entry, total_recettes, total_depenses)
    print("Envoi d'un nouveau message webhook...")
    try:
        res = requests.post(WEBHOOK_URL, json=embed)
        print(f"Discord POST status: {res.status_code}")
        if res.status_code in (200, 204):
            data = res.json()
            message_id = data['id']
            save_webhook_message_id(message_id)
            print(f"Message webhook envoyé, ID sauvegardé: {message_id}")
        else:
            print(f"Erreur webhook POST: {res.text}")
    except Exception as e:
        print(f"Exception lors de l'envoi webhook POST: {e}")

# Modifier l'embed existant
def edit_embed(message_id, entry, total_recettes, total_depenses):
    embed = create_embed(entry, total_recettes, total_depenses)
    url = f"{WEBHOOK_URL}/messages/{message_id}"
    print(f"PATCH webhook URL: {url}")
    print(f"Payload embed: {embed}")
    try:
        res = requests.patch(url, json=embed)
        print(f"Discord PATCH status: {res.status_code}")
        if res.status_code == 200:
            print("Embed modifié avec succès")
        else:
            print(f"Erreur PATCH : {res.text}")
            # fallback : supprimer et recréer
            print("Fallback: suppression + nouveau message")
            requests.delete(url)
            send_new_webhook(entry, total_recettes, total_depenses)
    except Exception as e:
        print(f"Exception lors du PATCH webhook : {e}")
        print("Fallback: suppression + nouveau message")
        try:
            requests.delete(url)
        except:
            pass
        send_new_webhook(entry, total_recettes, total_depenses)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/entries", methods=["GET"])
def get_entries():
    data = load_data()
    return jsonify(data)

@app.route("/api/entries", methods=["POST"])
def add_entry():
    new_entry = request.json
    data = load_data()
    data.append(new_entry)
    save_data(data)

    total_recettes = sum(float(d['montant']) for d in data if d['type'] == 'Recette')
    total_depenses = sum(float(d['montant']) for d in data if d['type'] == 'Dépense')
    message_id = load_webhook_message_id()
    if message_id:
        edit_embed(message_id, new_entry, total_recettes, total_depenses)
    else:
        send_new_webhook(new_entry, total_recettes, total_depenses)

    return jsonify({"status": "success"})

@app.route("/api/entries/<int:index>", methods=["PUT"])
def edit_entry(index):
    updated_entry = request.json
    data = load_data()
    if 0 <= index < len(data):
        data[index] = updated_entry
        save_data(data)

        total_recettes = sum(float(d['montant']) for d in data if d['type'] == 'Recette')
        total_depenses = sum(float(d['montant']) for d in data if d['type'] == 'Dépense')
        message_id = load_webhook_message_id()

        if message_id:
            last_entry = data[-1] if data else updated_entry
            edit_embed(message_id, last_entry, total_recettes, total_depenses)
        else:
            send_new_webhook(updated_entry, total_recettes, total_depenses)

        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Index out of range"}), 400

@app.route("/api/entries/<int:index>", methods=["DELETE"])
def delete_entry(index):
    data = load_data()
    if 0 <= index < len(data):
        data.pop(index)
        save_data(data)

        total_recettes = sum(float(d['montant']) for d in data if d['type'] == 'Recette')
        total_depenses = sum(float(d['montant']) for d in data if d['type'] == 'Dépense')
        message_id = load_webhook_message_id()

        if message_id:
            if data:
                last_entry = data[-1]
                edit_embed(message_id, last_entry, total_recettes, total_depenses)
            else:
                url = f"{WEBHOOK_URL}/messages/{message_id}"
                print(f"DELETE webhook URL: {url}")
                res = requests.delete(url)
                print(f"Discord DELETE status: {res.status_code}")
                if res.status_code == 204:
                    print("Message webhook supprimé")
                    os.remove(MESSAGE_ID_FILE)
                else:
                    print(f"Erreur DELETE webhook: {res.text}")
        else:
            print("Aucun message webhook à modifier ou supprimer")

        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Index out of range"}), 400

if __name__ == "__main__":
    app.run(debug=True)
