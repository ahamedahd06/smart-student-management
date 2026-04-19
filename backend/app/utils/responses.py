from flask import jsonify


def err(message: str, code: int = 400):
    return jsonify({"error": message}), code


def ok(data=None, code: int = 200):
    return jsonify(data if data is not None else {}), code
