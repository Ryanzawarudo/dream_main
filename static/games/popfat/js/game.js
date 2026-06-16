class PopCatGame {
    constructor() {
        this.clickCount = 0;
        this.timeLeft = 15;
        this.isGameActive = false;
        this.gameTimer = null;
        this.statsRecorded = false;

        this.clickTimestamps = [];
        this.clickRateHistory = [];
        this.chartUpdateInterval = null;

        this.initializeElements();
        this.attachEventListeners();
        this.initializeChart();
    }

    initializeElements() {
        this.comboDisplay = document.getElementById('combo');
        this.timerDisplay = document.getElementById('timer');
        this.gameButton = document.getElementById('gameButton');
        this.playAgainBtn = document.getElementById('playAgainBtn');
        this.gameOverScreen = document.getElementById('gameOver');
        this.finalScoreDisplay = document.getElementById('finalScore');
        this.canvas = document.getElementById('rateChart');
        this.ctx = this.canvas.getContext('2d');
        this.currentRateDisplay = document.getElementById('currentRate');
    }

    initializeChart() {
        this.drawChart();
    }

    attachEventListeners() {
        this.playAgainBtn.addEventListener('click', () => this.resetAndStart());
        this.gameButton.addEventListener('click', () => this.handleClick());
    }

    handleClick() {
        if (!this.isGameActive) {
            this.startGame();
        }

        if (!this.isGameActive) return;

        this.clickCount++;
        const now = Date.now();
        this.clickTimestamps.push(now);

        this.clickTimestamps = this.clickTimestamps.filter(
            timestamp => now - timestamp < 5000
        );

        this.updateDisplay();
        this.playClickAnimation();
        this.switchImage();
        this.drawChart();

        this.playSound();
    }

    calculateClickRate() {
        if (this.clickTimestamps.length === 0) return 0;

        const now = Date.now();
        const recentClicks = this.clickTimestamps.filter(
            timestamp => now - timestamp < 1000
        ).length;

        return recentClicks;
    }

    startGame() {
        this.isGameActive = true;
        this.gameOverScreen.style.display = 'none';
        this.gameButton.disabled = false;
        this.clickTimestamps = [];
        this.clickRateHistory = [];

        this.gameTimer = setInterval(() => this.updateTimer(), 1000);

        this.chartUpdateInterval = setInterval(() => {
            this.updateChartData();
            this.drawChart();
        }, 100);
    }

    resetAndStart() {
        this.statsRecorded = false;
        this.resetGameState();
        this.startGame();
    }

    resetGameState() {
        this.clickCount = 0;
        this.timeLeft = 15;
        this.isGameActive = false;

        if (this.gameTimer) {
            clearInterval(this.gameTimer);
        }
        if (this.chartUpdateInterval) {
            clearInterval(this.chartUpdateInterval);
        }

        this.clickTimestamps = [];
        this.clickRateHistory = [];
        this.updateDisplay();
        this.drawChart();
    }

    updateChartData() {
        const currentRate = this.calculateClickRate();
        this.clickRateHistory.push(currentRate);

        if (this.clickRateHistory.length > 50) {
            this.clickRateHistory.shift();
        }
    }

    drawChart() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.drawGrid();

        this.drawAxes();

        if (this.clickRateHistory.length > 0) {
            this.drawLine();
        }

        const currentRate = this.calculateClickRate();
        this.currentRateDisplay.textContent = `${currentRate} 次/秒`;
    }

    drawGrid() {
        const padding = 40;
        const chartWidth = this.canvas.width - 2 * padding;
        const chartHeight = this.canvas.height - 2 * padding;

        this.ctx.strokeStyle = '#e0e0e0';
        this.ctx.lineWidth = 1;

        const gridCountX = 5;
        for (let i = 0; i <= gridCountX; i++) {
            const x = padding + (chartWidth / gridCountX) * i;
            this.ctx.beginPath();
            this.ctx.moveTo(x, padding);
            this.ctx.lineTo(x, this.canvas.height - padding);
            this.ctx.stroke();
        }

        const gridCountY = 5;
        for (let i = 0; i <= gridCountY; i++) {
            const y = padding + (chartHeight / gridCountY) * i;
            this.ctx.beginPath();
            this.ctx.moveTo(padding, y);
            this.ctx.lineTo(this.canvas.width - padding, y);
            this.ctx.stroke();
        }
    }

    drawAxes() {
        const padding = 40;
        const chartWidth = this.canvas.width - 2 * padding;
        const chartHeight = this.canvas.height - 2 * padding;

        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 2;

        this.ctx.beginPath();
        this.ctx.moveTo(padding, this.canvas.height - padding);
        this.ctx.lineTo(this.canvas.width - padding, this.canvas.height - padding);
        this.ctx.stroke();

        this.ctx.beginPath();
        this.ctx.moveTo(padding, padding);
        this.ctx.lineTo(padding, this.canvas.height - padding);
        this.ctx.stroke();

        this.ctx.fillStyle = '#333';
        this.ctx.font = '12px Arial';
        this.ctx.textAlign = 'center';

        this.ctx.save();
        this.ctx.translate(15, this.canvas.height / 2);
        this.ctx.rotate(-Math.PI / 2);
        this.ctx.fillText('點擊速率 (次/秒)', 0, 0);
        this.ctx.restore();

        this.ctx.textAlign = 'center';
        this.ctx.fillText('時間 (秒)', this.canvas.width / 2, this.canvas.height - 10);

        this.ctx.font = 'bold 12px Arial';
        this.ctx.textAlign = 'right';
        const maxRate = 15;
        for (let i = 0; i <= 5; i++) {
            const y = this.canvas.height - padding - (chartHeight / 5) * i;
            const value = (maxRate / 5) * i;
            this.ctx.fillText(Math.round(value), padding - 10, y + 5);
        }
    }

    drawLine() {
        const padding = 40;
        const chartWidth = this.canvas.width - 2 * padding;
        const chartHeight = this.canvas.height - 2 * padding;
        const maxRate = 15;

        this.ctx.strokeStyle = '#667eea';
        this.ctx.lineWidth = 3;
        this.ctx.lineJoin = 'round';
        this.ctx.lineCap = 'round';

        const dataLength = this.clickRateHistory.length;

        this.ctx.beginPath();

        for (let i = 0; i < dataLength; i++) {
            const x = padding + (chartWidth / 50) * i;
            const value = this.clickRateHistory[i];
            const y = this.canvas.height - padding - (chartHeight / maxRate) * Math.min(value, maxRate);

            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        }

        this.ctx.stroke();

        this.ctx.fillStyle = 'rgba(102, 126, 234, 0.1)';
        this.ctx.lineTo(padding + chartWidth, this.canvas.height - padding);
        this.ctx.lineTo(padding, this.canvas.height - padding);
        this.ctx.closePath();
        this.ctx.fill();
    }

    switchImage() {
        const imgElement = document.getElementById('buttonImage');
        const currentSrc = imgElement.src;

        if (currentSrc.includes('open.png')) {
            imgElement.src = 'assets/images/close.png';
        } else {
            imgElement.src = 'assets/images/open.png';
        }

        setTimeout(() => {
            imgElement.src = 'assets/images/open.png';
        }, 100);
    }

    updateTimer() {
        this.timeLeft--;
        this.timerDisplay.textContent = `時間: ${this.timeLeft}秒`;

        if (this.timeLeft <= 0) {
            this.endGame();
        }
    }

    endGame() {
        if (!this.statsRecorded) {
            this.statsRecorded = true;
            notifyGamePlayed('popfat', {kg: this.clickCount});
        }
        this.isGameActive = false;
        clearInterval(this.gameTimer);
        if (this.chartUpdateInterval) {
            clearInterval(this.chartUpdateInterval);
        }
        this.gameButton.disabled = true;
        this.gameOverScreen.style.display = 'flex';
        this.finalScoreDisplay.textContent = this.clickCount;
    }

    updateDisplay() {
        this.comboDisplay.textContent = this.clickCount;
        this.timerDisplay.textContent = `時間: ${this.timeLeft}秒`;
    }

    playClickAnimation() {
        this.gameButton.style.transform = 'scale(0.9)';
        setTimeout(() => {
            this.gameButton.style.transform = 'scale(1)';
        }, 100);
    }

    playSound() {
        const audio = new Audio('assets/sounds/pop.mp3');
        audio.play();
    }
}

//呼叫父頁markGamePlayed(...) or 直接更新 localStorage or 發送 /api/game-stats 給後端
function notifyGamePlayed(gameId, details) {
    try {
        if (window.parent && window.parent !== window && typeof window.parent.markGamePlayed === 'function') {
            window.parent.markGamePlayed(gameId, details);
            return;
        }
        if (window.opener && typeof window.opener.markGamePlayed === 'function') {
            window.opener.markGamePlayed(gameId, details);
            return;
        }
        const played = JSON.parse(localStorage.getItem('playedGames') || '[]');
        if (!played.includes(gameId)) {
            played.push(gameId);
            localStorage.setItem('playedGames', JSON.stringify(played));
        }
        fetch('/api/game-stats', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ popfat_max_kg: {op:'max', val: Number(details && details.kg) || 0} })
        }).catch(() => {});
    } catch (err) {
        console.warn('notifyGamePlayed error', err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new PopCatGame();
});