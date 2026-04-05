# ai_car_lanefollowed
# 🚗 AI 智能駕駛小車 - 車道線實作專案

這是一個基於 Raspberry Pi 與 OpenCV 的自動循線小車專案，專為大學「AI 程式設計與應用」課程開發。本專案結合了卷積神經網路 (YOLOv8) 物件偵測與傳統電腦視覺演算法，實現穩定的自動駕駛與遠端監控。

## 🌟 專案亮點與技術實作
* **高階影像處理**：採用 HLS 色彩空間過濾與 Otsu 二值化，克服室內木地板反光挑戰。
* **精準控制演算法**：實作 PID 控制器，並加入 **Deadzone (容忍區間)** 與 **Clamping (限幅)** 機制，解決車輛蛇行與爆衝問題。
* **單邊跟隨邏輯**：具備線條遺失記憶模式，在車道線殘缺時仍能自動補償路徑。
* **多執行緒架構**：整合 Flask Web Server、YOLO 偵測與馬達控制，確保影像串流不卡頓。

## 📁 資料夾結構說明
* `app.py`: 主程式，負責 Flask 路由、影像串流與 PID 控制核心。
* `lane_detector.py`: 電腦視覺演算法，負責車道線辨識與誤差計算。
* `motor_control.py`: 硬體驅動層，控制 PCA9685 與馬達轉向。
* `index.html`: **(重要)** 本專案的期末結案報告網頁。
* `templates/`: 存放小車遠端中控台的 HTML 樣板。
* `static/`: 存放前端 CSS 樣式與控制邏輯 (main.js)。

## 🔗 相關連結
* **期末報告展示網頁 (GitHub Pages)**: [點此查看完整報告](https://kuoyenni02893.github.io/ai_car_lanefollowed/)
* **實作錄影 (YouTube)**: [觀看示範影片](https://youtube.com/shorts/1jLA6BuiSa4?feature=share))

## 👥 開發團隊
* I4A31 李牧鴻
* I4A32 郭妍妮
