const sizeMenu = document.getElementById('sizeMenu');
const boardWrapper = document.getElementById('boardWrapper');
const boardEl = document.getElementById('board');
const resultModal = document.getElementById('resultModal');
const resultTitle = document.getElementById('resultTitle');
const resultDetail = document.getElementById('resultDetail');
const restartButton = document.getElementById('restartButton');

let rows = 0;
let cols = 0;
let mines = 0;
let gameOver = false;
let grid = [];
let cells = [];
let revealedCount = 0;
let minesPlaced = false;

const sizes = {
  '6x6': 6,
  '9x9': 12,
  '12x12': 20
};

function createGrid(r, c) {
  rows = r;
  cols = c;
  mines = sizes[`${r}x${c}`] || Math.round(r * c * 0.15);
  gameOver = false;
  minesPlaced = false;
  revealedCount = 0;
  grid = Array.from({ length: rows }, () => Array.from({ length: cols }, () => ({ mine: false, revealed: false, mark: 0, count: 0 })));
  cells = [];
  renderBoard();
}

function placeMines(startRow, startCol) {
  const total = rows * cols;
  const startIndex = startRow * cols + startCol;
  const positions = Array.from({ length: total }, (_, i) => i).filter(i => i !== startIndex);
  for (let i = positions.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [positions[i], positions[j]] = [positions[j], positions[i]];
  }
  for (let placed = 0; placed < mines; placed++) {
    const idx = positions[placed];
    const r = Math.floor(idx / cols);
    const c = idx % cols;
    grid[r][c].mine = true;
  }
  minesPlaced = true;
}

function calculateCounts() {
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (grid[r][c].mine) continue;
      let count = 0;
      for (let dr = -1; dr <= 1; dr++) {
        for (let dc = -1; dc <= 1; dc++) {
          if (dr === 0 && dc === 0) continue;
          const nr = r + dr;
          const nc = c + dc;
          if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc].mine) {
            count += 1;
          }
        }
      }
      grid[r][c].count = count;
    }
  }
}

function renderBoard() {
  boardEl.innerHTML = '';
  boardWrapper.classList.remove('hidden');
  sizeMenu.classList.add('hidden');
  boardEl.style.setProperty('--cols', cols);
  const maxWidth = Math.min(window.innerWidth, 960) - 80;
  const maxHeight = window.innerHeight - 200;
  const cellSize = Math.max(22, Math.min(34, Math.floor(Math.min(maxWidth / cols, maxHeight / rows))));
  boardEl.style.setProperty('--cell-size', `${cellSize}px`);

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const tile = document.createElement('button');
      tile.type = 'button';
      tile.className = 'cell';
      tile.dataset.row = r;
      tile.dataset.col = c;
      tile.addEventListener('click', () => revealCell(r, c));
      tile.addEventListener('contextmenu', (event) => toggleMark(event, r, c));
      boardEl.appendChild(tile);
      cells.push(tile);
    }
  }
}

function revealCell(r, c) {
  if (gameOver) return;
  if (!minesPlaced) {
    placeMines(r, c);
    calculateCounts();
  }
  const tile = grid[r][c];
  if (tile.revealed || tile.mark !== 0) return;
  tile.revealed = true;
  revealedCount += 1;
  const cellEl = getCellElement(r, c);
  cellEl.classList.add('revealed');
  if (tile.mine) {
    cellEl.classList.add('mine');
    cellEl.textContent = '💣';
    endGame(false);
    return;
  }
  if (tile.count > 0) {
    cellEl.textContent = tile.count;
    cellEl.dataset.number = tile.count;
  }
  if (tile.count === 0) {
    cellEl.textContent = '';
    floodReveal(r, c);
  }
  if (revealedCount === rows * cols - mines) {
    endGame(true);
  }
}

function floodReveal(r, c) {
  for (let dr = -1; dr <= 1; dr++) {
    for (let dc = -1; dc <= 1; dc++) {
      const nr = r + dr;
      const nc = c + dc;
      if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
      const neighbor = grid[nr][nc];
      if (neighbor.revealed || neighbor.mark !== 0 || neighbor.mine) continue;
      neighbor.revealed = true;
      revealedCount += 1;
      const cellEl = getCellElement(nr, nc);
      cellEl.classList.add('revealed');
      if (neighbor.count > 0) {
        cellEl.textContent = neighbor.count;
        cellEl.dataset.number = neighbor.count;
      } else {
        cellEl.textContent = '';
        floodReveal(nr, nc);
      }
    }
  }
}

function toggleMark(event, r, c) {
  event.preventDefault();
  if (gameOver) return;
  const tile = grid[r][c];
  if (tile.revealed) return;
  tile.mark = (tile.mark + 1) % 3;
  const cellEl = getCellElement(r, c);
  cellEl.textContent = '';
  cellEl.classList.remove('flagged', 'question');
  if (tile.mark === 1) {
    cellEl.classList.add('flagged');
    cellEl.textContent = '🚩';
  } else if (tile.mark === 2) {
    cellEl.classList.add('question');
    cellEl.textContent = '❓';
  }
}

function getCellElement(r, c) {
  return boardEl.querySelector(`.cell[data-row="${r}"][data-col="${c}"]`);
}

function endGame(win) {
  gameOver = true;
  revealAllMines();
  resultModal.classList.add('active');
  if (win) {
    resultTitle.textContent = '🎉 勝利！';
    resultDetail.textContent = '你已成功掃除所有非地雷格子。';
  } else {
    resultTitle.textContent = '💥 失敗！';
    resultDetail.textContent = '很遺憾，你踩到地雷了。';
  }
}

function revealAllMines() {
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const tile = grid[r][c];
      const cellEl = getCellElement(r, c);
      if (!cellEl) continue;
      if (tile.mine && !tile.revealed) {
        cellEl.classList.add('revealed', 'mine');
        cellEl.textContent = '💣';
      }
      if (!tile.mine && tile.mark === 1) {
        cellEl.classList.add('revealed');
        cellEl.textContent = '❌';
      }
    }
  }
}

function resetGame() {
  resultModal.classList.remove('active');
  boardWrapper.classList.add('hidden');
  sizeMenu.classList.remove('hidden');
  boardEl.innerHTML = '';
  grid = [];
  cells = [];
  gameOver = false;
  revealedCount = 0;
}

document.querySelectorAll('.size-buttons button').forEach(button => {
  button.addEventListener('click', () => {
    const r = Number(button.dataset.rows);
    const c = Number(button.dataset.cols);
    createGrid(r, c);
  });
});

restartButton.addEventListener('click', resetGame);

document.addEventListener('contextmenu', (event) => {
  if (event.target.closest('.cell')) {
    event.preventDefault();
  }
});
