
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modèle de base de données
class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    description = db.Column(db.String(200))
    montant = db.Column(db.Float)
    type = db.Column(db.String(50))

# Création des tables au premier lancement
@app.before_first_request
def create_tables():
    db.create_all()

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/entries", methods=["GET"])
def get_entries():
    entries = Entry.query.all()
    return jsonify([{
        "date": e.date,
        "description": e.description,
        "montant": e.montant,
        "type": e.type
    } for e in entries])

@app.route("/api/entries", methods=["POST"])
def add_entry():
    data = request.json
    entry = Entry(
        date=data['date'],
        description=data['description'],
        montant=float(data['montant']),
        type=data['type']
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route("/api/entries/<int:index>", methods=["PUT"])
def update_entry(index):
    data = request.json
    entry = Entry.query.get(index)
    if entry:
        entry.date = data['date']
        entry.description = data['description']
        entry.montant = float(data['montant'])
        entry.type = data['type']
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Not found"}), 404

@app.route("/api/entries/<int:index>", methods=["DELETE"])
def delete_entry(index):
    entry = Entry.query.get(index)
    if entry:
        db.session.delete(entry)
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Not found"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
