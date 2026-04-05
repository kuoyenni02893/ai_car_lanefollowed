// 1. 車輛移動控制
function move(action) {
    console.log("執行移動: " + action);
    fetch('/move?action=' + action);
}

// 2. 舵機角度控制
function controlServo(direction) {
    console.log("舵機調整: " + direction);
    fetch('/servo?direction=' + direction);
}

// 3. 自動駕駛參數設定
function setParam(key, value) {
    console.log("更新參數: " + key + " = " + value);

    fetch(`/set_param?${key}=${value}`)
        .then(response => response.json())
        .then(data => {
            console.log("後端同步成功:", data);

            // 如果是切換模式，改變按鈕顏色
            if (key === 'mode') {
                document.getElementById('btn-manual').className = (value === 'manual' ? 'active' : '');
                document.getElementById('btn-auto').className = (value === 'auto' ? 'active' : '');

                if (value === 'auto') {
                    console.log("警告：自動駕駛已啟動，請隨時準備按下停止！");
                }
            }
        })
        .catch(err => console.error("參數更新失敗:", err));
}

// 4. 定期更新偏差量顯示 (每秒 10 次)
setInterval(() => {
    // 這裡可以透過 fetch('/status') 獲取即時 Error 值並更新 UI
    // 暫時由 app.py 直接在影像上繪製文字
}, 100);