import cv2
import numpy as np

class LaneDetector:
    def __init__(self):
        self.last_error = 0
        self.lane_width = 300  # 預存車道寬度，用於單邊推算中線

    def process_frame(self, frame):
        height, width = frame.shape[:2]
        center_x = width // 2

        # 1. ROI 切割：只看中下半部，避開天花板與車頭影子
        roi_top = int(height * 0.4)
        roi_bottom = int(height * 0.9)
        roi = frame[roi_top:roi_bottom, :]
        roi_height = roi.shape[0]

        # 2. 高亮度 + 低飽和度 先抓白線候選 (使用 HLS 色彩空間)
        hls = cv2.cvtColor(roi, cv2.COLOR_BGR2HLS)
        # HLS範圍：H(色相0-179), L(亮度0-255), S(飽和度0-255)
        # 設定白線特徵：亮度要高(>180)，飽和度要低(<60)
        lower_white = np.array([0, 180, 0])
        upper_white = np.array([179, 255, 60])
        white_mask = cv2.inRange(hls, lower_white, upper_white)

        # 3. 再加上 Canny 邊緣偵測
        edges = cv2.Canny(white_mask, 50, 150)

        # 4. 再用 HoughLinesP 強化真正的白線線段
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=30, minLineLength=20, maxLineGap=10)
        line_mask = np.zeros_like(white_mask)
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                # 優先找較粗的白色線段：畫上粗度為 5 的線條來強化特徵
                cv2.line(line_mask, (x1, y1), (x2, y2), 255, 5)

        # 5. 最後再用「細長輪廓」過濾掉地板反光與碎雜訊
        final_mask = np.zeros_like(white_mask)
        contours, _ = cv2.findContours(line_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # 過濾太小的亮斑
            if area > 100: 
                x, y, w, h = cv2.boundingRect(cnt)
                # 保留長條狀特徵 (高度或寬度具備一定規模)
                if h > 10 or w > 20: 
                    cv2.drawContours(final_mask, [cnt], -1, 255, -1)

        # 6. 分左右半區計算質心
        left_mask = np.zeros_like(final_mask)
        left_mask[:, :center_x] = final_mask[:, :center_x]
        right_mask = np.zeros_like(final_mask)
        right_mask[:, center_x:] = final_mask[:, center_x:]

        left_m = cv2.moments(left_mask)
        right_m = cv2.moments(right_mask)

        lx = int(left_m['m10'] / left_m['m00']) if left_m['m00'] > 0 else None
        rx = int(right_m['m10'] / right_m['m00']) if right_m['m00'] > 0 else None

        # 7. 中線估計與單邊跟隨邏輯
        guide_text = ""
        if lx is not None and rx is not None:
            # 同時保留雙線時的中線模式
            lane_center = (lx + rx) / 2
            guide_text = "Dual-line"
            self.lane_width = rx - lx  # 雙線時自動更新車道寬度記憶
        elif lx is not None:
            # 只看到左邊線時，目標中心自動往右偏一段
            lane_center = lx + (self.lane_width / 2)
            guide_text = "Single-side guide: left"
        elif rx is not None:
            # 只看到右邊線時，目標中心自動往左偏一段
            lane_center = rx - (self.lane_width / 2)
            guide_text = "Single-side guide: right"
        else:
            # 完全丟失線條時沿用上次誤差
            lane_center = center_x + self.last_error
            guide_text = "Memory mode"

        # 8. 計算偏差量 Error
        error = lane_center - center_x
        self.last_error = error

        # --- 產生含除錯資訊的畫面 ---
        # 建立一張全彩的黑圖，把處理完的 ROI 影像與文字疊加回去
        debug_frame = np.zeros((height, width, 3), dtype=np.uint8)
        roi_color = cv2.cvtColor(final_mask, cv2.COLOR_GRAY2BGR)
        
        # 畫出估計的中線位置 (紅點)
        cv2.circle(roi_color, (int(lane_center), roi_height//2), 8, (0, 0, 255), -1)
        # 顯示單邊跟隨的文字提示
        cv2.putText(roi_color, guide_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        debug_frame[roi_top:roi_bottom, :] = roi_color

        return error, debug_frame