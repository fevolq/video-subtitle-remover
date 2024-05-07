import os

from flask import Flask, request, jsonify, abort, send_file
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.server import process

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return 'Hello World'


@app.route('/submit', methods=['POST'])
def submit():
    if 'file' not in request.files:
        abort(400, description="No file part")

    file = request.files['file']
    if not file or file.filename == '':
        abort(400, description="No selected file")

    filename = file.filename
    area = request.args.get('area')
    print(f'submit接收请求：{area}')

    if area:
        area = [int(float(item.strip())) for item in area.split(',')]
        if len(area) != 4:
            abort(400, description="Error area")
    else:
        area = None

    worker = process.Worker(filename, file.stream)
    worker.set_sd(sub_area=tuple(area) if area else None)
    success = process.submit(worker)

    if success:
        return jsonify(code=200, data={'process_id': worker.process_id}), 200
    else:
        return jsonify(code=500, data={'process_id': worker.process_id}), 500


@app.route('/state', methods=['GET'])
def get_state():
    process_id = request.args.get('process_id')
    print(f'state接收请求：{process_id}')
    result = process.get_worker_state(process_id)
    if result is None:
        abort(404, description="Process not found")
    return jsonify(**result), 200


@app.route('/download', methods=['GET'])
def download():
    process_id = request.args.get('process_id')
    print(f'download接收请求：{process_id}')
    worker = process.get_worker(process_id)
    if not worker:
        abort(404, description="Process not found")
    output_path = worker.output_path
    filename = worker.filename

    if not worker.isFinished:
        abort(418, description="File not ready, please try later")
    else:
        process.remove_worker(process_id)

    if not os.path.isfile(output_path):
        abort(404, description="File not found")

    return send_file(output_path, as_attachment=True, download_name=filename)


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8090
    )
