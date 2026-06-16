const canvas = document.getElementById('tetris');
const context = canvas.getContext('2d');
const scoreElement = document.getElementById('score');
const levelElement = document.getElementById('level');
const linesElement = document.getElementById('lines');
const gameOverOverlay = document.getElementById('gameOverOverlay');
const finalScore = document.getElementById('finalScore');
const ratingElement = document.getElementById('finalRating');
const ratingMessage = document.getElementById('ratingMessage');
const bgMusic = document.getElementById('bgMusic');
const restartButton = document.getElementById('restartBtn');
let statsRecorded = false;

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
      body: JSON.stringify({ tetris_lines_cleared: {op:'inc', val: Number(details && details.lines) || 0} })
    }).catch(() => {});
  } catch (err) {
    console.warn('notifyGamePlayed error', err);
  }
}

const scale = 24;
canvas.width = 10 * scale;
canvas.height = 20 * scale;
context.scale(scale, scale);

const colors = [
  null,
  '#00f0f0',
  '#0000f0',
  '#f0a000',
  '#f0f000',
  '#00f000',
  '#a000f0',
  '#f00000',
  '#ffffff',
];

const pieces = {
  T: [
    [0, 0, 0],
    [1, 1, 1],
    [0, 1, 0],
  ],
  O: [
    [2, 2],
    [2, 2],
  ],
  L: [
    [0, 3, 0],
    [0, 3, 0],
    [0, 3, 3],
  ],
  J: [
    [0, 4, 0],
    [0, 4, 0],
    [4, 4, 0],
  ],
  I: [
    [0, 5, 0, 0],
    [0, 5, 0, 0],
    [0, 5, 0, 0],
    [0, 5, 0, 0],
  ],
  S: [
    [0, 6, 6],
    [6, 6, 0],
    [0, 0, 0],
  ],
  Z: [
    [7, 7, 0],
    [0, 7, 7],
    [0, 0, 0],
  ],
};

const player = {
  pos: { x: 0, y: 0 },
  matrix: null,
  nextMatrix: null,
  score: 0,
  level: 0,
  lines: 0,
  dropInterval: 1000,
  dropCounter: 0,
  lastTime: 0,
};

const arena = createMatrix(10, 20);
let gameOver = false;
let isClearing = false; 

function createMatrix(width, height) {
  return Array.from({ length: height }, () => new Array(width).fill(0));
}

function createPiece(type) {
  return pieces[type].map(row => row.slice());
}

function drawMatrix(matrix, offset) {
  matrix.forEach((row, y) => {
    row.forEach((value, x) => {
      if (!value) {
        return;
      }

      context.fillStyle = colors[value];
      context.fillRect(x + offset.x, y + offset.y, 1, 1);
      context.strokeStyle = '#0c0c22';
      context.lineWidth = 0.05;
      context.strokeRect(x + offset.x, y + offset.y, 1, 1);
    });
  });
}

function drawGrid() {
  context.strokeStyle = 'rgba(255,255,255,0.08)';
  context.lineWidth = 0.02;

  for (let x = 0; x <= 10; x++) {
    context.beginPath();
    context.moveTo(x, 0);
    context.lineTo(x, 20);
    context.stroke();
  }

  for (let y = 0; y <= 20; y++) {
    context.beginPath();
    context.moveTo(0, y);
    context.lineTo(10, y);
    context.stroke();
  }
}

function draw() {
  context.fillStyle = '#07111f';
  context.fillRect(0, 0, canvas.width / scale, canvas.height / scale);
  drawGrid();
  drawMatrix(arena, { x: 0, y: 0 });
  drawMatrix(player.matrix, player.pos);
}

function mergeArena() {
  player.matrix.forEach((row, y) => {
    row.forEach((value, x) => {
      if (value !== 0) {
        arena[y + player.pos.y][x + player.pos.x] = value;
      }
    });
  });
}

function collide() {
  const { matrix, pos } = player;

  for (let y = 0; y < matrix.length; y++) {
    for (let x = 0; x < matrix[y].length; x++) {
      if (matrix[y][x] !== 0 && (arena[y + pos.y] && arena[y + pos.y][x + pos.x]) !== 0) {
        return true;
      }
    }
  }

  return false;
}

function sweepArena() {
  const fullRows = [];
  for (let y = arena.length - 1; y >= 0; y--) {
    if (arena[y].every(cell => cell !== 0)) fullRows.push(y);
  }
  if (fullRows.length === 0) return;

  isClearing = true;
  let flash = 0;

  const flashInterval = setInterval(() => {
    fullRows.forEach(y => {
      arena[y].fill(flash % 2 === 0 ? 8 : 0);
    });
    flash++;

    if (flash > 5) {
      clearInterval(flashInterval);

      // 閃完之後才真正清除
      for (let i = fullRows.length - 1; i >= 0; i--) {
        arena.splice(fullRows[i], 1);
        arena.unshift(new Array(arena[0].length).fill(0));
      }

      const rowsCleared = fullRows.length;
      player.score += rowsCleared * 100 * rowsCleared;
      player.lines += rowsCleared;
      player.level = Math.min(10, Math.floor(player.lines / 10));
      player.dropInterval = 1000 - player.level * 80;
      updateScore();

      isClearing = false;
    }
  }, 60);
}

function playerDrop() {
  if (isClearing) return;  // ✅ 加這行，閃光期間不繼續掉落
  player.pos.y += 1;
  player.dropCounter = 0;

  if (collide()) {
    player.pos.y -= 1;
    mergeArena();
    sweepArena();
    resetPiece();
    updateScore();
  }
}

function playerMove(offset) {
  player.pos.x += offset;
  if (collide()) {
    player.pos.x -= offset;
  }
}

function rotate(matrix, direction) {
  for (let y = 0; y < matrix.length; y++) {
    for (let x = 0; x < y; x++) {
      [matrix[x][y], matrix[y][x]] = [matrix[y][x], matrix[x][y]];
    }
  }

  if (direction > 0) {
    matrix.forEach(row => row.reverse());
  } else {
    matrix.reverse();
  }
}

function playerRotate(direction) {
  const initialX = player.pos.x;
  let offset = 1;

  rotate(player.matrix, direction);

  while (collide()) {
    player.pos.x += offset;
    offset = -(offset + (offset > 0 ? 1 : -1));

    if (offset > player.matrix[0].length) {
      rotate(player.matrix, -direction);
      player.pos.x = initialX;
      return;
    }
  }
}

function hardDrop() {
  while (!collide()) {
    player.pos.y += 1;
  }

  player.pos.y -= 1;
  mergeArena();
  sweepArena();
  resetPiece();
  updateScore();
}

function resetPiece() {
  const pieceTypes = Object.keys(pieces);

  if (!player.nextMatrix) {
    player.nextMatrix = createPiece(pieceTypes[Math.floor(Math.random() * pieceTypes.length)]);
  }

  player.matrix = player.nextMatrix;
  player.nextMatrix = createPiece(pieceTypes[Math.floor(Math.random() * pieceTypes.length)]);
  player.pos.y = 0;
  player.pos.x = Math.floor((arena[0].length - player.matrix[0].length) / 2);
  drawNextPiece();  // ✅ 每次換新方塊時更新預覽

  if (collide()) {
    gameOver = true;
    showGameOver();
  }
}

function drawNextPiece() {
  const nc = document.getElementById('nextCanvas');
  const ctx = nc.getContext('2d');
  const s = 24;
  ctx.clearRect(0, 0, nc.width, nc.height);
  ctx.fillStyle = '#07111f';
  ctx.fillRect(0, 0, nc.width, nc.height);

  const m = player.nextMatrix;
  const ox = Math.floor((5 - m[0].length) / 2);
  const oy = Math.floor((5 - m.length) / 2);

  m.forEach((row, y) =>
    row.forEach((val, x) => {
      if (!val) return;
      ctx.fillStyle = colors[val];
      ctx.fillRect((x + ox) * s, (y + oy) * s, s, s);
      ctx.strokeStyle = '#0c0c22';
      ctx.lineWidth = 1.2;
      ctx.strokeRect((x + ox) * s, (y + oy) * s, s, s);
    })
  );
}

function update(time = 0) {
  if (gameOver) {
    return;
  }

  const deltaTime = time - player.lastTime;
  player.lastTime = time;
  player.dropCounter += deltaTime;

  if (player.dropCounter > player.dropInterval) {
    playerDrop();
  }

  draw();
  requestAnimationFrame(update);
}

function updateScore() {
  scoreElement.textContent = player.score;
  levelElement.textContent = player.level;
  linesElement.textContent = player.lines;
}

function getRating(score) {
  if (score >= 5000) {
    return 'A+';
  }
  if (score >= 3500) {
    return 'A';
  }
  if (score >= 2500) {
    return 'A-';
  }
  if (score >= 2000) {
    return 'B+';
  }
  if (score >= 1500) {
    return 'B';
  }
  if (score >= 1000) {
    return 'B-';
  }
  return 'C';
}

function showGameOver() {
  if (!statsRecorded) {
    statsRecorded = true;
    notifyGamePlayed('tetris', {lines: player.lines});
  }
  const rating = getRating(player.score);
  finalScore.textContent = player.score;
  ratingElement.textContent = rating;
  if (rating === 'C') {
    ratingMessage.classList.remove('hidden');
  } else {
    ratingMessage.classList.add('hidden');
  }
  gameOverOverlay.classList.remove('hidden');
}

function resetGame() {
  statsRecorded = false;
  arena.forEach(row => row.fill(0));
  player.score = 0;
  player.level = 0;
  player.lines = 0;
  player.dropInterval = 1000;
  player.dropCounter = 0;
  player.lastTime = 0;
  gameOver = false;
  gameOverOverlay.classList.add('hidden');
  ratingMessage.classList.add('hidden');
  resetPiece();
  updateScore();
  requestAnimationFrame(update);
}

function handleKeyDown(event) {
  if (gameOver) {
    return;
  }

  if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', ' '].includes(event.key)) {
    event.preventDefault();
  }

  switch (event.key) {
    case 'ArrowLeft':
      playerMove(-1);
      break;
    case 'ArrowRight':
      playerMove(1);
      break;
    case 'ArrowDown':
      playerDrop();
      break;
    case 'ArrowUp':
      playerRotate(1);
      break;
    case ' ': // space
      event.preventDefault();
      hardDrop();
      break;
    default:
      return;
  }
}

function init() {
  document.getElementById('startBtn').addEventListener('click', () => {
  document.getElementById('startOverlay').classList.add('hidden');
  resetGame();
});
  window.addEventListener('keydown', handleKeyDown);
  restartButton.addEventListener('click', resetGame);
  if (bgMusic) {
    bgMusic.volume = 0.25;
    bgMusic.play().catch(() => {
      /* 部分瀏覽器可能需要使用者操作才能播放 */
    });
  }
}

init();
