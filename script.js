const NUM_ROWS = 6;
const NUM_COLS = 5;
let currentRow = 0;
let currentGuess = "";
let currentMode = "infinity";
let isGameOver = false;
let secretHash = "";

const grid = document.getElementById("grid");
const rowElements = [];

const BACKEND_BASE_URL = "https://sportdle-backend.onrender.com";

function getStorageKey() {
  return `sportdle-${currentMode}`;
}

function saveProgress(guess, feedback, elim, info) {
  const key = `sportdle_${currentMode}_${secretHash}`;
  const existing = JSON.parse(localStorage.getItem(key) || "[]");
  existing.push({ guess, feedback, elim, info });
  localStorage.setItem(key, JSON.stringify(existing));
}

function loadProgress() {
  const key = `sportdle_${currentMode}_${secretHash}`;
  const saved = JSON.parse(localStorage.getItem(key) || "[]");

  for (const entry of saved) {
    restoreRow(entry);
    currentRow++;
  }

  if (saved.length >= NUM_ROWS || saved.some(row => row.feedback === "GGGGG")) {
    isGameOver = true;
  }
}

function clearProgress() {
  localStorage.removeItem(getStorageKey());
}

function resetBoard() {
  currentRow = 0;
  currentGuess = "";
  isGameOver = false;

  document.getElementById("grid").innerHTML = "";
  rowElements.length = 0;

  for (let i = 0; i < NUM_ROWS; i++) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("row-wrapper");

    const leftScore = document.createElement("div");
    leftScore.classList.add("score-cell");
    leftScore.id = `score-left-${i}`;

    const row = document.createElement("div");
    row.classList.add("row");
    for (let j = 0; j < NUM_COLS; j++) {
      const box = document.createElement("div");
      box.classList.add("box");
      row.appendChild(box);
    }

    const rightScore = document.createElement("div");
    rightScore.classList.add("score-cell");
    rightScore.id = `score-right-${i}`;

    wrapper.appendChild(leftScore);
    wrapper.appendChild(row);
    wrapper.appendChild(rightScore);
    grid.appendChild(wrapper);

    rowElements.push(row);
  }
}

function restoreRow(entry) {
  const row = rowElements[currentRow];
  const guess = entry.guess.toUpperCase();
  const feedback = entry.feedback;

  for (let i = 0; i < NUM_COLS; i++) {
    const box = row.children[i];
    box.textContent = guess[i];
    box.classList.add(
      feedback[i] === "G" ? "green" :
      feedback[i] === "Y" ? "yellow" : "gray"
    );
  }

  document.getElementById(`score-left-${currentRow}`).innerHTML = getScoreMeterHTML(entry.elim);
  document.getElementById(`score-right-${currentRow}`).innerHTML = getScoreMeterHTML(entry.info);
}

function resetKeyboardColors() {
  const keys = document.querySelectorAll("#keyboard span");
  keys.forEach(key => {
    key.classList.remove("gray", "yellow", "green");
  });
  Object.keys(keyColors).forEach(k => delete keyColors[k]);
}

function changeMode() {
  const mode = document.getElementById("mode").value;
  currentMode = mode;

  // Show/hide "New Word" button based on mode
  const newWordBtn = document.getElementById("new-word-btn");
  newWordBtn.style.display = (mode === "infinity") ? "inline-block" : "none";

  fetch(`${BACKEND_BASE_URL}/start_game?mode=${mode}`)
    .then(res => res.json())
    .then(data => {
      secretHash = data.secretHash;
      resetBoard();
      resetKeyboardColors();
      clearProgress();
      loadProgress();
    });
}


function getScoreMeterHTML(score) {
  let color = "red";
  if (score > 90) color = "purple";
  else if (score > 75) color = "blue";
  else if (score > 50) color = "green";
  else if (score > 25) color = "yellow";

  return `
    <div class="score-wrapper">
      <div class="score-value">${score}</div>
      <div class="meter">
        <div class="fill ${color}" style="width: ${score}%;"></div>
      </div>
    </div>
  `;
}

document.addEventListener("keydown", (e) => {
  if (currentRow >= NUM_ROWS || isGameOver) return;

  const isLetter = /^[a-zA-Z]$/.test(e.key);
  const row = rowElements[currentRow];

  if (isLetter && currentGuess.length < NUM_COLS) {
    currentGuess += e.key.toLowerCase();
    row.children[currentGuess.length - 1].textContent = e.key.toUpperCase();
  } else if (e.key === "Backspace" && currentGuess.length > 0) {
    row.children[currentGuess.length - 1].textContent = "";
    currentGuess = currentGuess.slice(0, -1);
  } else if (e.key === "Enter" && currentGuess.length === NUM_COLS) {
    submitGuess(currentGuess);
  }
});

function submitGuess(guess) {
  fetch(`${BACKEND_BASE_URL}/score`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ guess: guess })
  })
    .then((res) => res.json())
    .then((data) => {
      if (!data.valid) {
        alert("❌ Not a valid word!");
        return;
      }

      const { feedback, elimination_score, info_score, correct, secretHash: hashBack } = data;
      secretHash = hashBack;
      const row = rowElements[currentRow];

      for (let i = 0; i < NUM_COLS; i++) {
        const box = row.children[i];
        if (feedback[i] === "G") {
          box.classList.add("green");
        } else if (feedback[i] === "Y") {
          box.classList.add("yellow");
        } else {
          box.classList.add("gray");
        }
      }

      document.getElementById(`score-left-${currentRow}`).innerHTML = getScoreMeterHTML(elimination_score);
      document.getElementById(`score-right-${currentRow}`).innerHTML = getScoreMeterHTML(info_score);
      updateKeyboardColors(guess, feedback);

      saveProgress(guess, feedback, elimination_score, info_score);

      if (correct) {
        isGameOver = true;
        setTimeout(() => alert("🎉 You guessed it!"), 100);
      } else if (currentRow + 1 >= NUM_ROWS) {
        isGameOver = true;
        showEndMessage();
      }

      currentRow++;
      currentGuess = "";
    })
    .catch((err) => {
      console.error("Error:", err);
      alert("Server error. Is the Flask backend running?");
    });
}

function showEndMessage() {
  fetch(`${BACKEND_BASE_URL}/secret`)
    .then(res => res.json())
    .then(data => {
      alert(`❌ Game over. The word was: ${data.secret.toUpperCase()}`);
    });
}

window.onload = () => {
  const selector = document.getElementById("mode");
  currentMode = selector ? selector.value : "infinity";

  fetch(`${BACKEND_BASE_URL}/start_game?mode=${currentMode}`)
    .then(res => res.json())
    .then(data => {
      secretHash = data.secretHash;
      resetBoard();
      resetKeyboardColors();
      loadProgress();
      renderKeyboard();
    });
};

function renderKeyboard() {
  const keyboard = document.getElementById("keyboard");
  keyboard.innerHTML = "";

  const rows = [
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
    ["Enter", "Z", "X", "C", "V", "B", "N", "M", "Backspace"]
  ];

  for (const letters of rows) {
    const rowDiv = document.createElement("div");
    rowDiv.classList.add("keyboard-row");

    for (const letter of letters) {
      const key = document.createElement("span");
      key.textContent = letter === "Backspace" ? "⌫" : (letter === "Enter" ? "⏎" : letter);
      key.dataset.key = letter;
      key.id = `key-${letter}`;
      key.classList.add("keyboard-key");
      key.addEventListener("click", () => handleKeyClick(letter));
      rowDiv.appendChild(key);
    }

    keyboard.appendChild(rowDiv);
  }
}

function handleKeyClick(key) {
  if (isGameOver || currentRow >= NUM_ROWS) return;

  const row = rowElements[currentRow];

  if (/^[a-zA-Z]$/.test(key) && currentGuess.length < NUM_COLS) {
    currentGuess += key.toLowerCase();
    row.children[currentGuess.length - 1].textContent = key.toUpperCase();
  } else if (key === "Backspace" && currentGuess.length > 0) {
    row.children[currentGuess.length - 1].textContent = "";
    currentGuess = currentGuess.slice(0, -1);
  } else if (key === "Enter" && currentGuess.length === NUM_COLS) {
    submitGuess(currentGuess);
  }
}

const keyColors = {};

function updateKeyboardColors(guess, feedback) {
  for (let i = 0; i < guess.length; i++) {
    const letter = guess[i].toUpperCase();
    const fb = feedback[i];

    let newColor = "";
    if (fb === "G") newColor = "green";
    else if (fb === "Y") newColor = "yellow";
    else newColor = "gray";

    const current = keyColors[letter];
    const priority = { "green": 3, "yellow": 2, "gray": 1 };
    if (!current || priority[newColor] > priority[current]) {
      keyColors[letter] = newColor;
      const keyEl = document.getElementById(`key-${letter}`);
      if (keyEl) {
        keyEl.classList.remove("gray", "yellow", "green");
        keyEl.classList.add(newColor);
      }
    }
  }
}
function startNewInfinityGame() {
  if (currentMode !== "infinity") return;

  fetch(`${BACKEND_BASE_URL}/start_game?mode=infinity`)
    .then(res => res.json())
    .then(data => {
      secretHash = data.secretHash;
      resetBoard();
      resetKeyboardColors();
      clearProgress();
    });
}
