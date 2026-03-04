import os
import hashlib
from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def hash_machine(machine_id):
    return hashlib.sha256(machine_id.encode()).hexdigest()

@app.route("/")
def home():
    return "License Server Running"

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    key = data.get("key")
    machine_id = data.get("machine_id")

    if not key or not machine_id:
        return jsonify({"status": "error", "message": "Thiếu dữ liệu"}), 400

    machine_hash = hash_machine(machine_id)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT machine_id FROM licenses WHERE license_key=%s", (key,))
    result = cur.fetchone()

    if not result:
        return jsonify({"status": "invalid", "message": "Key không tồn tại"}), 403

    saved_machine = result[0]

    # Nếu chưa kích hoạt
    if saved_machine is None:
        cur.execute(
            "UPDATE licenses SET machine_id=%s WHERE license_key=%s",
            (machine_hash, key)
        )
        conn.commit()
        return jsonify({"status": "activated", "message": "Kích hoạt thành công"})

    # Nếu đã dùng rồi
    if saved_machine == machine_hash:
        return jsonify({"status": "valid", "message": "Key hợp lệ"})

    return jsonify({"status": "used", "message": "Key đã dùng trên máy khác"}), 403

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
