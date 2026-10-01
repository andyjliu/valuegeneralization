<script>
  // Canvas heatmap shared by Sections 1 and 2.
  // color(i, j) -> css color; rows/cols are label arrays.
  let {
    rows = [],
    cols = [],
    color = () => '#eee',
    diag = () => false,          // (i, j) -> bool: outline self-cells
    selected = null,             // {i, j}
    rowDivider = null,           // draw a dashed rule after this many rows
    colDivider = null,
    onselect = () => {},
    onhover = () => {},
    version = 0,                 // bump to force a redraw when color() changes
    ariaLabel = 'matrix',
    showRowLabels = true,
    showColLabels = true,
    cellSize = null,             // fixed cell size (px); otherwise fit to width
    rowGutter = 196,
    hoverExt = null,             // crosshair driven by a linked matrix
  } = $props();

  const LABEL_FONT = '10px Inter, system-ui, sans-serif';
  const MAXCH = 32;
  let wrap = $state();
  let canvas = $state();
  let width = $state(900);
  let hover = $state(null);

  const clipLabel = (s) => (s.length > MAXCH ? s.slice(0, MAXCH - 1) + '…' : s);
  let gutterL = $derived(showRowLabels ? rowGutter : 2);
  let gutterT = $derived(showColLabels ? 176 : 2);
  let cell = $derived(cellSize ?? Math.max(6, Math.min(15, Math.floor((width - gutterL - 8) / Math.max(1, cols.length)))));
  let W = $derived(gutterL + cell * cols.length + 8);
  let H = $derived(gutterT + cell * rows.length + 8);

  function draw() {
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    // cells (1px surface gap when cells are big enough)
    const gap = cell >= 9 ? 1 : 0;
    for (let i = 0; i < rows.length; i++) {
      for (let j = 0; j < cols.length; j++) {
        ctx.fillStyle = color(i, j);
        ctx.fillRect(gutterL + j * cell, gutterT + i * cell, cell - gap, cell - gap);
      }
    }
    // self cells
    ctx.strokeStyle = 'rgba(11,11,11,0.55)';
    ctx.lineWidth = 1;
    for (let i = 0; i < rows.length; i++)
      for (let j = 0; j < cols.length; j++)
        if (diag(i, j)) ctx.strokeRect(gutterL + j * cell + 0.5, gutterT + i * cell + 0.5, cell - gap - 1, cell - gap - 1);
    // dividers
    ctx.setLineDash([4, 3]);
    ctx.strokeStyle = '#52514e';
    if (colDivider != null && colDivider < cols.length) {
      const x = gutterL + colDivider * cell - gap / 2;
      ctx.beginPath(); ctx.moveTo(x, gutterT - 4); ctx.lineTo(x, gutterT + rows.length * cell); ctx.stroke();
    }
    if (rowDivider != null && rowDivider < rows.length) {
      const y = gutterT + rowDivider * cell - gap / 2;
      ctx.beginPath(); ctx.moveTo(gutterL - 4, y); ctx.lineTo(gutterL + cols.length * cell, y); ctx.stroke();
    }
    ctx.setLineDash([]);
    // crosshair
    const hi = hover ?? hoverExt ?? selected;
    if (hi) {
      ctx.fillStyle = 'rgba(11,11,11,0.06)';
      ctx.fillRect(gutterL, gutterT + hi.i * cell, cols.length * cell, cell);
      ctx.fillRect(gutterL + hi.j * cell, gutterT, cell, rows.length * cell);
    }
    if (selected) {
      ctx.strokeStyle = '#0b0b0b';
      ctx.lineWidth = 2;
      ctx.strokeRect(gutterL + selected.j * cell - 1, gutterT + selected.i * cell - 1, cell + 1, cell + 1);
    }
    // labels
    ctx.font = LABEL_FONT;
    ctx.textBaseline = 'middle';
    const fs = Math.min(10, Math.max(8, cell - 1));
    ctx.font = `${Math.max(7, fs)}px Inter, system-ui, sans-serif`;
    ctx.textAlign = 'right';
    if (showRowLabels) for (let i = 0; i < rows.length; i++) {
      const on = hi && hi.i === i;
      ctx.fillStyle = on ? '#0b0b0b' : '#52514e';
      ctx.font = `${on ? 600 : 400} ${Math.max(7, fs)}px Inter, system-ui, sans-serif`;
      ctx.fillText(clipLabel(rows[i]), gutterL - 6, gutterT + i * cell + cell / 2);
    }
    ctx.textAlign = 'left';
    if (showColLabels) for (let j = 0; j < cols.length; j++) {
      const on = hi && hi.j === j;
      ctx.save();
      ctx.translate(gutterL + j * cell + cell / 2, gutterT - 6);
      ctx.rotate(-Math.PI / 2);
      ctx.fillStyle = on ? '#0b0b0b' : '#52514e';
      ctx.font = `${on ? 600 : 400} ${Math.max(7, fs)}px Inter, system-ui, sans-serif`;
      ctx.fillText(clipLabel(cols[j]), 0, 0);
      ctx.restore();
    }
    // axis titles
    ctx.fillStyle = '#52514e';
    ctx.font = '600 14px Inter, system-ui, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    if (showColLabels) ctx.fillText('EVALUATED ON →', gutterL, 10);
    if (showRowLabels && showColLabels) {
      ctx.save();
      ctx.translate(10, gutterT);
      ctx.rotate(-Math.PI / 2);
      ctx.textAlign = 'right';
      ctx.fillText('TRAINED ON →', 0, 0);
      ctx.restore();
    }
  }

  $effect(() => {
    // redraw on any dependency change
    void [W, H, cell, rows, cols, selected, hover, hoverExt, version, color, rowDivider, colDivider, gutterL, gutterT];
    draw();
  });

  function cellAt(ev) {
    const r = canvas.getBoundingClientRect();
    const x = ev.clientX - r.left - gutterL, y = ev.clientY - r.top - gutterT;
    const j = Math.floor(x / cell), i = Math.floor(y / cell);
    if (i < 0 || j < 0 || i >= rows.length || j >= cols.length) return null;
    return { i, j };
  }
  function onmove(ev) {
    const c = cellAt(ev);
    if (c?.i !== hover?.i || c?.j !== hover?.j) hover = c;
    onhover(c, ev);
  }
  function onleave() { hover = null; onhover(null); }
  function onclick(ev) { const c = cellAt(ev); if (c) onselect(c); }
  function onkeydown(ev) {
    const s = selected ?? { i: 0, j: 0 };
    const d = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] }[ev.key];
    if (d) {
      ev.preventDefault();
      onselect({ i: Math.max(0, Math.min(rows.length - 1, s.i + d[0])), j: Math.max(0, Math.min(cols.length - 1, s.j + d[1])) });
    } else if (ev.key === 'Escape') onselect(null);
  }
</script>

<div class="matrix-wrap" bind:this={wrap} bind:clientWidth={width} style:width={cellSize ? "auto" : "100%"}>
  <canvas
    bind:this={canvas}
    tabindex="0"
    aria-label={ariaLabel + '. Use arrow keys to move between cells.'}
    onmousemove={onmove}
    onmouseleave={onleave}
    onclick={onclick}
    onkeydown={onkeydown}
    style="cursor: crosshair"
  ></canvas>
</div>

<style>
  .matrix-wrap { width: 100%; overflow-x: auto; }
  canvas { display: block; outline: none; }
  canvas:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }
</style>
