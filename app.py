from flask import Flask, jsonify, request, send_file, send_from_directory
import os
import json
from datetime import datetime
from text_to_image import ImageGenerator
from utils import storage

IMAGES_PATH = os.environ.get("IMAGES_PATH", "/tmp/photo-generator/images")
NUM_GEN = int(os.environ.get("NUM_GEN", "1"))

app = Flask(__name__, static_folder="./frontend/dist", static_url_path="/")

# Serve frontend static files
@app.errorhandler(404)
def not_found(e):
    return app.send_static_file("index.html")


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/status")
def status():
    return jsonify({"status": "ok"})


@app.route("/api/predictions", methods=["POST"])
def create_prediction():
    data = request.data or "{}"
    body = json.loads(data)
    id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    storage.make_dirs(id)

    prediction = {"id": id, "prompt": body.get("prompt")}
    storage.write_json(prediction, f"{id}/prediction.json")

    images = []

    for index in range(NUM_GEN):
        image_json = {
            "status": "QUEUED",
            "progress": 0,
            "file": f"/api/images/{id}/image-{index}.jpg"
        }
        images.append(image_json)
        storage.write_json(image_json, f"{id}/image-{index}.json")
        ImageGenerator(id, index, body.get("prompt"))

    prediction["images"] = images
    return jsonify(prediction)


@app.route("/api/predictions/<string:id>", methods=["GET"])
def get_prediction(id):
    prediction = storage.read_json(f"{id}/prediction.json")

    image_files = sorted(storage.list_files(id, f"*image-*.json"))
    images = []
    for index, fname in enumerate(image_files):
        img = storage.read_json(fname)
        images.append(img)

    prediction["images"] = images

    return jsonify(prediction)


@app.route("/api/images/<path:path>", methods=["GET"])
def get_image(path):
    return send_file(storage.read_file(path), mimetype="image/jpeg")


if __name__ == "__main__":
    port = os.environ.get("FLASK_PORT") or 8080
    port = int(port)

    app.run(port=port, host="0.0.0.0")
