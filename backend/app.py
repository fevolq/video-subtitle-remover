import os
import sys
import urllib.parse

import uvicorn
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import FileResponse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.server import process

app = FastAPI()


@app.get('/')
async def index():
    return 'Hello World'


@app.post("/submit")
async def submit(
        file: UploadFile = File(...),
        area: str = Query(None),
):
    print(f'submit接受请求：{area}')
    if area:
        area = [float(item.strip()) for item in area.split(',')]
        if len(area) != 4:
            raise HTTPException(status_code=400, detail="Error area")

    worker = process.Worker(file.filename, file.file)
    worker.set_sd(sub_area=tuple(area) if area else None)
    success = process.submit(worker)

    return {
        'code': 200 if success else 500,
        'data': {
            'process_id': worker.process_id
        }
    }


@app.get("/state")
async def get_state(process_id: str):
    print(f'state接受请求：{process_id}')
    result = process.get_worker_state(process_id)
    return {
        'code': 200,
        **result
    }


@app.get("/download")
async def download(process_id: str):
    print(f'download接受请求：{process_id}')
    worker = process.get_worker(process_id)

    if not worker:
        raise HTTPException(status_code=404, detail="Process not found")

    output_path = worker.input_path
    filename = urllib.parse.quote(worker.filename)  # 对文件名进行编码，否则中文名会异常

    if not worker.sd.isFinished:
        raise HTTPException(status_code=418, detail="File not ready, please try later")
    process.remove_worker(process_id)

    if not os.path.isfile(output_path):
        raise HTTPException(status_code=418, detail="File not found")

    return FileResponse(
        path=output_path,
        media_type="application/octet-stream",  # 可以根据文件类型进行调整
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


if __name__ == '__main__':
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8090,
    )
