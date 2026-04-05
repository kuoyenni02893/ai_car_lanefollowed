from flask import Flask, render_template, Response, request, jsonify
import cv2, time, threading
from picamera2 import Picamera2
from ultralytics import YOLO
from motor_control import MotorControl
from lane_detector import LaneDetector
from pid_controller import PIDController

app = Flask(__name__)
robot = MotorControl()
lane_det = LaneDetector()
pid_ctrl = PIDController(kp=0.15, ki=0.0, kd=0.25)
model = YOLO('yolo_model.pt')

status = {"mode": "manual", "base_speed": 35, "yolo_enabled": True}

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

frame_count = 0  # 確保這行放在 gen_frames 外面或作為全域變數

def gen_frames():
    global frame_count
    while True:
        try:
            # 取得影像並校正格式與方向
            frame = picam2.capture_array()
            if frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
            frame = cv2.rotate(frame, cv2.ROTATE_180)

            # 1. 每一幀都執行車道辨識，確保駕駛穩定
            error, debug_frame = lane_det.process_frame(frame)

            if status["mode"] == "auto":
                # --- 新增的穩定控制邏輯 ---
                # (a) 容忍區間 (Deadzone)：誤差在 15 像素內不修正，防止直路蛇行抖動
                if abs(error) < 15:
                    error = 0

                # 計算 PID 轉向力道
                steering = pid_ctrl.calculate(error)

                # (b) 轉向限幅 (Clamping)：限制最大轉向力道在正負 20，防止爆衝與極端甩尾
                max_steer = 20
                if steering > max_steer:
                    steering = max_steer
                elif steering < -max_steer:
                    steering = -max_steer

                # 將基礎速度與限制後的轉向力道送給馬達
                robot.steer(status["base_speed"], steering)

            # 2. 限制 YOLO 推論頻率：每 10 幀才執行一次辨識，防當機
            frame_count += 1
            if frame_count % 10 == 0:
                # 減小 imgsz 解析度可大幅提升速度
                results = model(frame, imgsz=160, conf=0.5, verbose=False)
                # 將辨識結果框疊加回畫面上
                frame = results[0].plot()

            # 3. 疊加 Error 文字資訊，方便你從網頁監控
            cv2.putText(frame, f"Error: {error:.1f}", (10, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # 4. 影像編碼與輸出給網頁
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 40])
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

        except Exception as e:
            print(f"影像串流錯誤: {e}")
            break

@app.route('/')
def index(): return render_template('index.html')

@app.route('/video_feed')
def video_feed(): return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_param')
def set_param():
    # 接收網頁傳來的參數
    mode = request.args.get('mode')
    speed = request.args.get('speed')
    kp = request.args.get('kp')
    kd = request.args.get('kd')
    ki = request.args.get('ki')

    if mode: status["mode"] = mode
    if speed: status["base_speed"] = int(speed)
    if kp: pid_ctrl.kp = float(kp)
    if kd: pid_ctrl.kd = float(kd)
    if ki: pid_ctrl.ki = float(ki)

    # 切換回手動時立即停車，確保安全
    if status["mode"] == "manual":
        robot.stop()

    return jsonify(status)

@app.route('/move')
def car_move():
    action = request.args.get('action')
    # 如果在自動模式下，不接受手動指令
    if status["mode"] == "auto":
        return "In Auto Mode"

    if action == 'forward':
        robot.steer(status["base_speed"], 0)
    elif action == 'reverse':
        for i in range(4): robot.motor_run(i, 'backward', status["base_speed"])
    elif action == 'left':
        # 轉彎時動力稍微提高 20
        robot.motor_run(0, 'backward', status["base_speed"]+20)
        robot.motor_run(2, 'backward', status["base_speed"]+20)
        robot.motor_run(1, 'forward', status["base_speed"]+20)
        robot.motor_run(3, 'forward', status["base_speed"]+20)
    elif action == 'right':
        robot.motor_run(1, 'backward', status["base_speed"]+20)
        robot.motor_run(3, 'backward', status["base_speed"]+20)
        robot.motor_run(0, 'forward', status["base_speed"]+20)
        robot.motor_run(2, 'forward', status["base_speed"]+20)
    elif action == 'stop':
        robot.stop()
    return "OK"

@app.route('/servo')
def servo_control():
    # 舵機控制：9號上下，10號左右
    direction = request.args.get('direction')
    if direction == 'up': robot.set_servo_angle(9, 25)
    elif direction == 'down': robot.set_servo_angle(9, 50)
    elif direction == 'left': robot.set_servo_angle(10, 110)
    elif direction == 'right': robot.set_servo_angle(10, 70)
    elif direction == 'home':
        robot.set_servo_angle(9, 40); robot.set_servo_angle(10, 90)
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)