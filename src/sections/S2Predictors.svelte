<script>
  import Matrix from '../lib/Matrix.svelte';
  import Controls from '../lib/Controls.svelte';
  import DivLegend from '../lib/DivLegend.svelte';
  import { load, armId, divColor, MODEL_LABEL, METHOD_LABEL } from '../lib/data.js';

  let model = $state('qwen');
  let method = $state('dpo');
  let view = $state('wins');
  let focusPred = $state('persona');
  let values = $state([]);
  let board = $state(null);
  let P = $state(null);
  let G = $state(null);   // same row/col frame as P for the first 49 rows
  let sel = $state({ i: 0, j: 1 });
  let tip = $state(null);
  let scatter = $state();

  let arm = $derived(armId(model, method));
  load('values.json').then((v) => (values = v));
  load('leaderboard.json').then((b) => (board = b));
  $effect(() => {
    const a = arm;
    load(`predictors_${a}.json`).then((p) => { if (a === arm) P = p; });
    load(`g_${a}.json`).then((g) => { if (a === arm) G = g; });
    load(`g_${a}.json`).then((g) => { if (a === arm) G = g; });
  });

  const predIds = $derived(board ? board.preds.map((p) => p.id) : []);
  const label = (id) => board?.preds.find((p) => p.id === id)?.label ?? id;
  let nC = $derived(P ? P.cols.length : 0);

  // per-cell winner (lowest rank-residual) + margin to runner-up
  let winners = $derived.by(() => {
    if (!P) return null;
    const n = P.rows.length * nC;
    const win = new Array(n).fill(null), margin = new Float32Array(n);
    for (let k = 0; k < n; k++) {
      if (P.gpct[k] == null) continue;
      let best = null, b1 = 1e9, b2 = 1e9;
      for (const p of predIds) {
        const r = P.preds[p].resid[k];
        if (r == null) continue;
        if (r < b1) { b2 = b1; b1 = r; best = p; } else if (r < b2) b2 = r;
      }
      win[k] = best;
      margin[k] = b2 - b1;
    }
    return { win, margin };
  });
  let winShare = $derived.by(() => {
    if (!winners) return {};
    const c = {}; let t = 0;
    for (const w of winners.win) if (w) { c[w] = (c[w] ?? 0) + 1; t++; }
    return Object.fromEntries(Object.entries(c).map(([k, v]) => [k, v / t]));
  });

  const WIN = '#2a78d6';
  let color = $derived.by(() => {
    if (!P) return () => '#eee';
    if (view === 'g') {
      return (i, j) => (G ? divColor(G.g[i * G.cols.length + j] / 1000) : '#eee');
    }
    return (i, j) => {
      const k = i * nC + j;
      if (P.gpct[k] == null) return '#ffffff';
      if (winners.win[k] !== focusPred) return '#f0efec';
      const t = Math.min(1, 0.25 + winners.margin[k] / 25);
      return `rgba(42,120,214,${t.toFixed(3)})`;
    };
  });
  let diag = $derived(P ? (i, j) => P.rows[i] === P.cols[j] : () => false);
  let rowLabels = $derived(P && values.length ? P.rows.map((r) => values[r].name) : []);
  let colLabels = $derived(P && values.length ? P.cols.map((c) => values[c].name) : []);

  function onhover(c, ev) {
    if (!c || !P) { tip = null; return; }
    const k = c.i * nC + c.j;
    tip = { x: ev.clientX, y: ev.clientY, v1: P.rows[c.i], v2: P.cols[c.j], w: winners?.win[k], g: P.gpct[k] };
  }

  let cell = $derived.by(() => {
    if (!P || !sel || !board) return null;
    const k = sel.i * nC + sel.j;
    const g = P.gpct[k];
    if (g == null) return { self: true, v1: P.rows[sel.i], v2: P.cols[sel.j] };
    const ranked = predIds
      .map((p) => ({ id: p, cos: P.preds[p].cos[k], pct: P.preds[p].pct[k], resid: P.preds[p].resid[k] }))
      .filter((r) => r.resid != null)
      .sort((a, b) => a.resid - b.resid);
    return { k, g, v1: P.rows[sel.i], v2: P.cols[sel.j], ranked };
  });

  // bars
  let bars = $derived(board ? predIds.map((p) => ({ id: p, rho: board.rho[arm][p], ci: board.ci[arm][p], agg: board.aggregate[p].mean_rho })).sort((a, b) => b.rho - a.rho) : []);
  const BW = 520, BH = 30, LX = 140;
  const xs = (v) => LX + (v / 1) * (BW - LX - 20);

  // mini scatter: pct(pred) vs pct(G) for the winning predictor
  $effect(() => {
    if (!scatter || !cell || cell.self || !P) return;
    const p = cell.ranked[0].id;
    const dpr = window.devicePixelRatio || 1, S = 200, pad = 24;
    scatter.width = S * dpr; scatter.height = S * dpr;
    scatter.style.width = S + 'px'; scatter.style.height = S + 'px';
    const ctx = scatter.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, S, S);
    const sx = (v) => pad + (v / 100) * (S - pad - 6), sy = (v) => S - pad - (v / 100) * (S - pad - 6);
    ctx.strokeStyle = '#c3c2b7'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad, 6); ctx.lineTo(pad, S - pad); ctx.lineTo(S - 6, S - pad); ctx.stroke();
    ctx.strokeStyle = '#e1e0d9'; ctx.beginPath(); ctx.moveTo(sx(0), sy(0)); ctx.lineTo(sx(100), sy(100)); ctx.stroke();
    ctx.fillStyle = 'rgba(82,81,78,0.18)';
    const pp = P.preds[p].pct;
    for (let k = 0; k < pp.length; k++) if (pp[k] != null && P.gpct[k] != null) ctx.fillRect(sx(pp[k]) - 1, sy(P.gpct[k]) - 1, 2, 2);
    ctx.fillStyle = WIN; ctx.strokeStyle = '#fcfcfb'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(sx(pp[cell.k]), sy(cell.g), 5, 0, 7); ctx.stroke(); ctx.fill();
    ctx.fillStyle = '#898781'; ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'center'; ctx.fillText(`${label(p)} similarity pct.`, pad + (S - pad) / 2, S - 6);
    ctx.save(); ctx.translate(10, (S - pad) / 2); ctx.rotate(-Math.PI / 2); ctx.fillText('G percentile', 0, 0); ctx.restore();
  });
  const ord = (n) => { const s = ['th', 'st', 'nd', 'rd'], v = n % 100; return n + (s[(v - 20) % 10] || s[v] || s[0]); };
</script>

<section class="chapter" id="predictors">
  <div class="prose">
    <div class="eyebrow">Part 2</div>
    <h2>Benchmarking value representations</h2>
    <p>
      Computing G requires training a model on every value. Can we predict it <em>before</em> training? We compare
      five candidate value representations: value description embeddings (<strong>Description-Embd</strong>),
      behavioral sentence embeddings (<strong>Behavior-Embd</strong>), persona vectors (<strong>Persona</strong>),
      gradient update directions (<strong>Gradient</strong>), and weight steering (<strong>Weight</strong>). For
      each pair of values we compute the cosine similarity between their representations, and score each method
      by the Spearman rank correlation between that similarity and G across all pairs of values.
    </p>
    <p>
      Methods based on model activations when applying values in context significantly outperform those based on
      textual descriptions. The very low correlation (ρ = 0.06) for description embeddings suggests that
      alignment generalization is driven by behavioral patterns that value descriptions do not capture; the best
      activation-based methods reach ρ = 0.46. Below, <strong>click a cell</strong> to see which representation
      ranked that particular pair closest to where it really fell.
    </p>
  </div>

  <div class="figure">
    <div class="layout">
      <div class="rail ui toolbar-row">
        <Controls bind:model bind:method>
          <div class="ctl">
            <span class="ctl-label">Matrix shows</span>
            <div class="seg" role="group" aria-label="Matrix view">
              <button aria-pressed={view === 'wins'} onclick={() => (view = 'wins')}>Best predictor</button>
              <button aria-pressed={view === 'g'} onclick={() => (view = 'g')}>G value</button>
            </div>
          </div>
          {#if view === 'wins' && board}
            <div class="ctl">
              <span class="ctl-label">Highlight pairs where … predicts best</span>
              <div class="predlist">
                {#each predIds as p}
                  <button class="predbtn" aria-pressed={focusPred === p} onclick={() => (focusPred = p)}>
                    <span>{label(p)}</span><span class="num muted">{Math.round((winShare[p] ?? 0) * 100)}%</span>
                  </button>
                {/each}
              </div>
              <p class="note muted">% of value pairs each representation ranks most accurately. Darker = wins by a wider margin.</p>
            </div>
          {:else}
            <DivLegend />
          {/if}
        </Controls>
      </div>

      <div class="main">
        {#if board}
          <div class="board card">
            <div class="board-head ui">
              <span class="eyebrow">Spearman <span style="text-transform:none">ρ</span> with G · {MODEL_LABEL[model]} {METHOD_LABEL[method]}</span>
              <span class="legend-inline muted"><span class="tick"></span> 4-setting mean <span class="ceil"></span> ceiling</span>
            </div>
            <svg viewBox="0 0 {BW} {bars.length * BH + 26}" width="100%" role="img" aria-label="Predictor correlations">
              {#each [0, 0.2, 0.4, 0.6, 0.8, 1] as t}
                <line x1={xs(t)} x2={xs(t)} y1="0" y2={bars.length * BH} stroke="#e1e0d9" />
                <text x={xs(t)} y={bars.length * BH + 16} text-anchor="middle" class="axis num">{t.toFixed(1)}</text>
              {/each}
              {#each bars as b, r}
                <g transform="translate(0,{r * BH})">
                  <text x={LX - 10} y={BH / 2 + 4} text-anchor="end" class="blabel">{label(b.id)}</text>
                  <rect x={xs(0)} y={BH / 2 - 7} width={Math.max(0, xs(b.rho) - xs(0))} height="14" rx="3" fill={b.id === cell?.ranked?.[0]?.id ? '#1c5cab' : '#2a78d6'} />
                  <line x1={xs(b.ci[0])} x2={xs(b.ci[1])} y1={BH / 2} y2={BH / 2} stroke="#0b0b0b" stroke-width="1.25" />
                  <line x1={xs(b.agg)} x2={xs(b.agg)} y1={BH / 2 - 10} y2={BH / 2 + 10} stroke="#0b0b0b" stroke-width="2" />
                  <text x={Math.max(xs(b.rho), xs(b.ci[1])) + 8} y={BH / 2 + 4} class="bval num">{b.rho.toFixed(2)}</text>
                </g>
              {/each}
              <line x1={xs(board.ceiling[arm])} x2={xs(board.ceiling[arm])} y1="-2" y2={bars.length * BH} stroke="#898781" stroke-dasharray="4 3" />
              <text x={xs(board.ceiling[arm]) - 4} y="10" text-anchor="end" class="axis">ceiling {board.ceiling[arm].toFixed(2)}</text>
            </svg>
            <p class="note muted ui">Whiskers: 95% bootstrap CI over trained values. Ceiling: how well any symmetric similarity could do (G vs. its own symmetrized version).</p>
          </div>
        {/if}
        {#if P && values.length}
          <Matrix
            rows={rowLabels}
            cols={colLabels}
            {color}
            {diag}
            selected={sel}
            colDivider={49}
            onselect={(c) => c && (sel = c)}
            {onhover}
            ariaLabel="Per-pair best predictor matrix"
          />
        {/if}
      </div>

      <aside class="detail card ui">
        {#if cell && values.length}
          <h3 class="headline"><span class="v">{values[cell.v1].name}</span> → <span class="v">{values[cell.v2].name}</span></h3>
          {#if cell.self}
            <p class="muted">Training and evaluating on the same value isn't a transfer cell, so predictors aren't scored here.</p>
          {:else}
            <p class="ink2">Real effect ranks in the <strong>{ord(cell.g)} percentile</strong> of all pairs. Each row shows where a representation's cosine similarity ranks this pair; closer to the line is better.</p>
            <svg viewBox="0 0 360 {cell.ranked.length * 26 + 30}" width="100%" role="img" aria-label="Percentile comparison">
              {#each [0, 25, 50, 75, 100] as t}
                <text x={130 + t * 2.1} y={cell.ranked.length * 26 + 22} text-anchor="middle" class="axis num">{t}</text>
              {/each}
              <line x1={130 + cell.g * 2.1} x2={130 + cell.g * 2.1} y1="0" y2={cell.ranked.length * 26 + 6} stroke="#0b0b0b" stroke-width="1.5" />
              {#each cell.ranked as r, n}
                <g transform="translate(0,{n * 26 + 14})">
                  <text x="120" y="4" text-anchor="end" class="blabel" font-weight={n === 0 ? 600 : 400}>{label(r.id)}</text>
                  <line x1="130" x2="340" y1="0" y2="0" stroke="#e1e0d9" />
                  <line x1={130 + cell.g * 2.1} x2={130 + r.pct * 2.1} y1="0" y2="0" stroke={n === 0 ? WIN : '#c3c2b7'} stroke-width="3" stroke-linecap="round" />
                  <circle cx={130 + r.pct * 2.1} cy="0" r="5" fill={n === 0 ? WIN : '#898781'} stroke="#fcfcfb" stroke-width="2" />
                </g>
              {/each}
            </svg>
            <table class="rank num">
              <thead><tr><th></th><th>Representation</th><th>cos</th><th>pct</th><th>off by</th></tr></thead>
              <tbody>
                {#each cell.ranked as r, n}
                  <tr class:best={n === 0}><td>{n + 1}</td><td>{label(r.id)}</td><td>{r.cos?.toFixed(2)}</td><td>{r.pct}</td><td>{r.resid}</td></tr>
                {/each}
              </tbody>
            </table>
            <div class="sc">
              <span class="eyebrow">This pair vs. all pairs ({label(cell.ranked[0].id)})</span>
              <canvas bind:this={scatter}></canvas>
            </div>
          {/if}
        {:else}
          <p class="muted">Click a cell to compare predictors.</p>
        {/if}
      </aside>
    </div>
  </div>

  {#if tip && values.length}
    <div class="tooltip" style="left:{tip.x + 14}px; top:{tip.y + 14}px">
      <strong>{values[tip.v1].name}</strong> → {values[tip.v2].name}<br />
      {#if tip.g == null}self cell{:else}G pct {tip.g} · best: {label(tip.w)}{/if}
    </div>
  {/if}
</section>

<style>
  .layout { display: grid; grid-template-columns: minmax(0, 1fr) 380px; gap: 24px; align-items: start; }
  .rail { grid-column: 1 / -1; }
    .main { display: flex; flex-direction: column; gap: 20px; min-width: 0; }
  .board { padding: 14px 16px 8px; max-width: 620px; }
  .board-head { display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 8px; margin-bottom: 6px; }
  .legend-inline { font-size: 11px; display: inline-flex; align-items: center; gap: 6px; }
  .legend-inline .tick { display: inline-block; width: 2px; height: 12px; background: var(--ink); }
  .legend-inline .ceil { display: inline-block; width: 0; height: 12px; border-left: 1px dashed var(--muted); margin-left: 6px; }
  svg .axis { font: 10px Inter, sans-serif; fill: #898781; }
  svg .blabel { font: 12px Inter, sans-serif; fill: #0b0b0b; }
  svg .bval { font: 600 12px Inter, sans-serif; fill: #0b0b0b; }
  .note { font-size: 11.5px; margin: 6px 0 0; max-width: 520px; }
  .predlist { display: flex; flex-wrap: wrap; gap: 3px; }
  .predbtn { display: flex; gap: 8px; justify-content: space-between; border: 1px solid transparent; background: none; border-radius: 6px; padding: 5px 8px; cursor: pointer; font-family: var(--sans); font-size: 13px; color: var(--ink-2); text-align: left; }
  .predbtn:hover { background: var(--surface-2); }
  .predbtn[aria-pressed='true'] { background: var(--accent-soft); border-color: var(--accent); color: var(--ink); font-weight: 600; }
  .detail { position: sticky; top: calc(var(--header-h) + 20px); padding: 18px; max-height: calc(100vh - var(--header-h) - 40px); overflow-y: auto; }
  .headline { font-size: 16px; font-weight: 500; margin: 0 0 8px; }
  .headline .v { font-weight: 700; }
  .detail p { font-size: 13px; margin: 0 0 8px; }
  .rank { width: 100%; border-collapse: collapse; font-size: 12.5px; margin: 8px 0 14px; }
  .rank th { text-align: left; font-weight: 600; color: var(--muted); font-size: 11px; border-bottom: 1px solid var(--grid); padding: 4px; }
  .rank td { padding: 4px; border-bottom: 1px solid var(--grid); }
  .rank tr.best td { font-weight: 600; color: #1c5cab; }
  .sc canvas { display: block; margin-top: 6px; }
  @media (max-width: 1180px) {
    .layout { grid-template-columns: minmax(0, 1fr); }
    .detail { position: static; max-height: none; }
  }
</style>
