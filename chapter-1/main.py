import base64
import io
import os
import uuid

import numpy as np
from fastapi import FastAPI, UploadFile
from fastapi import File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool
from PIL import Image
from pydantic import BaseModel
from ultralytics import YOLO

SAVE_DIR = "static"
os.makedirs(SAVE_DIR, exist_ok=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

model = YOLO("yolo26n.pt") # yolo26n-seg.pt도 사용 가능 


class DetectionResult(BaseModel):
    message: str
    image: str | None = None   # base64 응답
    url: str | None = None     # URL 응답


@app.get("/") # 기본 GET 엔드포인트 
async def index():
    return {"message": "Hello FastAPI"}


@app.post("/detect", response_model=DetectionResult)
async def detect(
    message: str = Form(...),        # 텍스트 메시지
    responseType: str = Form(...),   # 응답 유형 (base64 | url)
    file: UploadFile = File(...)     # 업로드 이미지
):
    try:
        # 1. 파일 → PIL 이미지 변환
        image = Image.open(
            io.BytesIO(await file.read())
        ).convert("RGB")

        # 2. YOLO 추론 (blocking → threadpool)
        result = await run_in_threadpool(
            lambda: model(image, conf=0.3, verbose=False)[0]
        )

        # 3. 탐지 결과 이미지 생성 (numpy)
        #    - 객체가 있으면 bounding box 포함
        #    - 없으면 원본 이미지 사용
        img = result.plot() if result.boxes else np.array(image)
        img = img[:, :, ::-1] # BGR → RGB 변환 (OpenCV → PIL)

        # 4. Base64 응답
        if responseType == "base64":
            buffer = io.BytesIO()

            # numpy → JPEG → 메모리 저장
            Image.fromarray(img).save(
                buffer, format="JPEG", quality=70
            )

            return DetectionResult(
                message="response: " + message,
                image=base64.b64encode(
                    buffer.getvalue()
                ).decode()
            )

        # 5. URL 응답
        elif responseType == "url":
            # UUID 파일명 생성
            filename = f"{uuid.uuid4()}.jpg"
            filepath = os.path.join(SAVE_DIR, filename)

            # 이미지 파일 저장
            Image.fromarray(img).save(
                filepath, format="JPEG", quality=90
            )

            return DetectionResult(
                message="response: " + message,
                url=f"http://localhost:8000/static/{filename}"
            )

        # 6. 잘못된 요청 처리
        else:
            raise HTTPException(
                status_code=400,
                detail="invalid responseType"
            )

    # 7. 예외 처리
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
