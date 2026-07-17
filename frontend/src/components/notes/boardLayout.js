export const BOARD = {
  cols: 4,
  cellW: 340,
  cellH: 320,
  margin: 110,
};

export function todayIsoDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function dateHash(value) {
  let hash = 2166136261;

  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }

  return hash >>> 0;
}

function rand01(hash, salt) {
  let mixed = Math.imul(hash ^ salt, 2654435761);
  mixed ^= mixed >>> 13;
  mixed = Math.imul(mixed, 1274126177);
  mixed ^= mixed >>> 16;
  return (mixed >>> 0) / 4294967296;
}

export function boardSize(noteCount) {
  const rows = Math.max(2, Math.ceil(noteCount / BOARD.cols));

  return {
    width: BOARD.margin * 2 + BOARD.cols * BOARD.cellW,
    height: BOARD.margin * 2 + rows * BOARD.cellH,
  };
}

export function noteAppearance(dateString, index) {
  const hash = dateHash(dateString);
  const column = index % BOARD.cols;
  const row = Math.floor(index / BOARD.cols);
  const width = 236 + rand01(hash, 4) * 52;
  const height = 212 + rand01(hash, 5) * 56;
  const offsetX = (rand01(hash, 2) - 0.5) * 48;
  const offsetY = (rand01(hash, 3) - 0.5) * 44;
  const rotation = (rand01(hash, 1) - 0.5) * 7.5;
  const paperRoll = rand01(hash, 6);
  const paper = paperRoll < 0.22 ? 'paper-kraft' : paperRoll < 0.5 ? 'paper-cream' : 'paper-white';
  const fastenerRoll = rand01(hash, 7);
  const fastener = fastenerRoll < 0.46 ? 'pin' : fastenerRoll < 0.78 ? 'clip' : 'tape';
  const pinTint = rand01(hash, 8) < 0.5 ? 'pin-red' : 'pin-brass';
  const centerX = BOARD.margin + column * BOARD.cellW + BOARD.cellW / 2 + offsetX;
  const centerY = BOARD.margin + row * BOARD.cellH + BOARD.cellH / 2 + offsetY;

  return {
    width,
    height,
    rotation,
    paper,
    fastener,
    pinTint,
    centerX,
    centerY,
    left: centerX - width / 2,
    top: centerY - height / 2,
  };
}

const STAMP_MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];

export function formatStamp(dateString) {
  const [year, month, day] = dateString.split('-').map(Number);
  const base = `${day} ${STAMP_MONTHS[month - 1]}`;
  return year === new Date().getFullYear() ? base : `${base} ${year}`;
}

export function formatFullDate(dateString) {
  const date = new Date(`${dateString}T00:00:00`);
  return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
}
