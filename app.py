import os
import hashlib
from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")


# =========================
# KẾT NỐI DATABASE
# =========================
def get_connection():
    return psycopg2.connect(DATABASE_URL)


# =========================
# HASH MACHINE ID
# =========================
def hash_machine(machine_id):
    return hashlib.sha256(machine_id.encode()).hexdigest()


# =========================
# TEST SERVER
# =========================
@app.route("/")
def home():
    return "License Server Running OK"


# =========================
# VERIFY LICENSE
# =========================
@app.route("/verify", methods=["POST"])
def verify():
    data = request.get_json()

    key = data.get("key")
    machine_id = data.get("machine_id")

    if not key or not machine_id:
        return jsonify({
            "status": "error",
            "message": "Thiếu key hoặc machine_id"
        }), 400

    machine_hash = hash_machine(machine_id)

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute(
        "SELECT machine_id FROM licenses WHERE license_key=%s",
        (key,)
    )

    result = cur.fetchone()

    # Key không tồn tại
    if not result:
        cur.close()
        conn.close()
        return jsonify({
            "status": "invalid",
            "message": "Key không tồn tại"
        }), 403

    saved_machine = result["machine_id"]

    # Chưa kích hoạt
    if saved_machine is None:
        cur.execute(
            "UPDATE licenses SET machine_id=%s WHERE license_key=%s",
            (machine_hash, key)
        )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "status": "activated",
            "message": "Kích hoạt thành công"
        })

    # Đã kích hoạt đúng máy
    if saved_machine == machine_hash:
        cur.close()
        conn.close()

        return jsonify({
            "status": "valid",
            "message": "Key hợp lệ"
        })

    # Đã dùng máy khác
    cur.close()
    conn.close()
    return jsonify({
        "status": "used",
        "message": "Key đã được dùng trên máy khác"
    }), 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
