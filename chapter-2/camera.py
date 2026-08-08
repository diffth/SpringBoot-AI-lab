import base64
import json
import time

import cv2
import paho.mqtt.client as mqtt
from ultralytics import YOLO

BROKER = "localhost"
PORT = 1883
TOPIC = "/camera/objects"

JPEG_QUALITY = 70
SEND_INTERVAL = 0.2   # 초 (5 FPS 전송)

model = YOLO("yolo26n.pt")

def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Connected:", reason_code)

def on_disconnect(client, userdata, flags, reason_code, properties=None):
    print("Disconnected:", reason_code)

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

client.on_connect = on_connect
client.on_disconnect = on_disconnect

client.connect(BROKER, PORT)
client.loop_start()

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

last_sent = 0

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, verbose=False)[0]
        image = results.plot()

        now = time.time()
        if now - last_sent >= SEND_INTERVAL:
            last_sent = now

            # JPEG 인코딩
            success, buffer = cv2.imencode(
                ".jpg",
                image,
                [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
            )

            if success:
                jpg_bytes = buffer.tobytes()
                jpg_base64 = base64.b64encode(jpg_bytes).decode()

                payload = json.dumps({
                    "timestamp": now,
                    "image": jpg_base64
                })

                # QoS 0 → 빠름 / QoS 1 → 안정성
                client.publish(TOPIC, payload, qos=0)

        cv2.imshow("Frame", image)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    client.loop_stop()
    client.disconnect()