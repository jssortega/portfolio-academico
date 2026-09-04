async function cargarEstado() {
  const respuesta = await fetch("/game/state");
  const estado = await respuesta.json();
  renderizarEstado(estado);
}

function renderizarEstado(estado) {
  renderizarCabecera(estado);
  renderizarJugadores(estado);
  renderizarTurno(estado);
  renderizarTablero(estado.board);
  renderizarHistorial(estado.history);
  renderizarResultado(estado);
}

function renderizarCabecera(estado) {
  const badge = document.getElementById("status-badge");
  badge.textContent = `Estado: ${estado.status}`;
}

function renderizarJugadores(estado) {
  document.getElementById("player-x-card").innerHTML = `
    <h2>Jugador X</h2>
    <p>${estado.players.X ?? "Esperando jugador"}</p>
  `;

  document.getElementById("player-o-card").innerHTML = `
    <h2>Jugador O</h2>
    <p>${estado.players.O ?? "Esperando jugador"}</p>
  `;
}

function renderizarTurno(estado) {
  let texto = "Esperando";
  if (estado.status === "playing") texto = estado.current_turn;
  if (estado.status === "finished") texto = "-";

  document.getElementById("turn-card").innerHTML = `
    <h2>Turno actual</h2>
    <p>${texto}</p>
  `;
}

function renderizarTablero(board) {
  const grid = document.getElementById("board-grid");
  grid.innerHTML = "";

  board.forEach((valor) => {
    const celda = document.createElement("div");
    celda.className = "cell";
    if (valor === "X") celda.classList.add("x");
    if (valor === "O") celda.classList.add("o");
    celda.textContent = valor;
    grid.appendChild(celda);
  });
}

function renderizarHistorial(history) {
  const panel = document.getElementById("history-panel");

  if (!history.length) {
    panel.innerHTML = "<h2>Historial de movimientos</h2><p>Sin movimientos aún</p>";
    return;
  }

  panel.innerHTML = "<h2>Historial de movimientos</h2>" +
    history.map(item => `
      <div class="history-item">
        Turno ${item.turn}: ${item.symbol} → posición ${item.position}
      </div>
    `).join("");
}

function renderizarResultado(estado) {
  const panel = document.getElementById("result-panel");

  let texto = "En curso";
  if (estado.status === "finished" && estado.result === "draw") texto = "Empate";
  if (estado.status === "finished" && estado.result === "win") texto = `Ganador: ${estado.winner}`;
  if (estado.status === "finished" && estado.result === "aborted") texto = "Abortada";

  panel.innerHTML = `<h2>Resultado</h2><p>${texto}</p>`;
}

window.addEventListener("load", cargarEstado);
setInterval(cargarEstado, 1000);