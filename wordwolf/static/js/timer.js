let timerIntervalId = null;
let remainingSeconds = 0;
const TIME_DISPLAY_ID = 'time-display';

export function formatTime(totalSeconds) {
    if (totalSeconds < 0) {
        totalSeconds = 0;
    }
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    
    // 常に2桁表示を保証
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}


export function updateTimeDisplay(seconds) {
    const displayElement = document.getElementById(TIME_DISPLAY_ID);
    if (displayElement) {
        displayElement.textContent = formatTime(seconds);

        // 時間切れが近い場合、色を変える
        if (seconds <= 30 && seconds > 0) {
            displayElement.closest('h4').classList.add('text-danger');
        } else if (seconds <= 0) {
            displayElement.closest('h4').classList.remove('text-danger');
            displayElement.closest('h4').classList.add('text-muted');
        } else {
             displayElement.closest('h4').classList.remove('text-danger', 'text-muted');
        }
    }
}

export function stopTimer() {
    if (timerIntervalId !== null) {
        clearInterval(timerIntervalId);
        timerIntervalId = null;
        console.log("タイマーが停止しました。");
    }
}


export function startTimer(durationSeconds, onTimeUp) {
    stopTimer();
    
    remainingSeconds = durationSeconds;
    updateTimeDisplay(remainingSeconds);

    if (remainingSeconds <= 0) {
        if (onTimeUp) onTimeUp();
        return;
    }

    timerIntervalId = setInterval(() => {
        remainingSeconds -= 1;
        updateTimeDisplay(remainingSeconds);

        if (remainingSeconds <= 0) {
            stopTimer();
            console.log("時間切れです！");
            if (onTimeUp) {
                onTimeUp();
            }
        }
    }, 1000);
    
    console.log(`タイマーが ${durationSeconds}秒 で開始されました。`);
}