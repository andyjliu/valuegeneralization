<script>
  import Matrix from '../lib/Matrix.svelte';
  import Controls from '../lib/Controls.svelte';
  import { load, armId, divColor, PRED_HEX, MODEL_LABEL, METHOD_LABEL } from '../lib/data.js';

  let model = $state('qwen');
  let method = $state('dpo');
  let pred = $state('persona');
  let values = $state([]);
  let board = $state(null);
  let P = $state(null);
  let sel = $state({ i: 0, j: 1 });
  let hover = $state(null);
  let tip = $state(null);
  let scatter = $state();
  let pairW = $state(1200);

  let arm = $derived(armId(model, method));
  load('values.json').then((v) => (values = v));
  load('leaderboard.json').then((b) => (board = b));
  $effect(() => {
    const a = arm;
    load(`predictors_${a}.json`).then((p) => { if (a === arm) P = p; });
  });

  const predIds = $derived(board ? board.preds.map((p) => p.id) : []);
  const label = (id) => board?.preds.find((p) => p.id === id)?.label ?? id;
  let nC = $derived(P ? P.cols.length : 0);

  // both matrices are drawn in rank space (Spearman compares ranks), on G's diverging scale
  const rankColor = (pct) => (pct == null ? '#ffffff' : divColor((pct - 50) / 62.5));
  let colorG = $derived(P ? (i, j) => rankColor(P.gpct[i * nC + j]) : () => '#eee');
  let colorP = $derived(P ? (i, j) => rankColor(P.preds[pred].pct[i * nC + j]) : () => '#eee');
  let diag = $derived(P ? (i, j) => P.rows[i] === P.cols[j] : () => false);
  let rowLabels = $derived(P && values.length ? P.rows.map((r) => values[r].name) : []);
  let colLabels = $derived(P && values.length ? P.cols.map((c) => values[c].name) : []);

  // two matrices side by side: left carries the row labels
  const ROWG = 150, GAP = 28;
  let cellSize = $derived(Math.max(4, Math.min(11, Math.floor((pairW - ROWG - GAP - 8) / (2 * Math.max(1, nC))))));

  function onhover(c, ev) {
    hover = c;
    if (!c || !P) { tip = null; return; }
    const k = c.i * nC + c.j;
    tip = { x: ev.clientX, y: ev.clientY, v1: P.rows[c.i], v2: P.cols[c.j], g: P.gpct[k], p: P.preds[pred].pct[k] };
  }
  const onselect = (c) => c && (sel = c);

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
  const xs = (v) => LX + v * (BW - LX - 20);

  // mini scatter: pct(selected predictor) vs pct(G), this pair highlighted
  $effect(() => {
    if (!scatter || !cell || cell.self || !P) return;
    const p = pred;
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
    ctx.fillStyle = PRED_HEX[p]; ctx.strokeStyle = '#fcfcfb'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(sx(pp[cell.k]), sy(cell.g), 5, 0, 7); ctx.stroke(); ctx.fill();
    ctx.fillStyle = '#52514e'; ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'center'; ctx.fillText(`${label(p)} similarity (pct.)`, pad + (S - pad) / 2, S - 6);
    ctx.save(); ctx.translate(10, (S - pad) / 2); ctx.rotate(-Math.PI / 2); ctx.fillText('G (pct.)', 0, 0); ctx.restore();
  });
  const ord = (n) => { const s = ['th', 'st', 'nd', 'rd'], v = n % 100; return n + (s[(v - 20) % 10] || s[v] || s[0]); };
  const legendStops = Array.from({ length: 21 }, (_, k) => k * 5);

  // one-line method summaries, from §4.1 of the paper
  const PRED_DESC = {
    persona: 'Difference in mean activations between pro-value and anti-value responses, taken at the layer that steers the model most strongly (<a href="https://arxiv.org/abs/2507.21509">Chen et al., 2025</a>).',
    grad_proj: 'Gradient of the DPO loss on each value\'s preference pairs, averaged into the direction the model would update when fine-tuned on that value (<a href="https://www.lesswrong.com/posts/b8u6XrphyHAXA4hBi/where-do-llm-values-come-from">Sun et al., 2026</a>).',
    sentemb_behavior: 'Difference between sentence embeddings (<a href="https://huggingface.co/sentence-transformers/all-mpnet-base-v2">all-mpnet-base-v2</a>) of pro-value and anti-value responses, averaged across elicitation prompts.',
    weight_steer: 'Difference in weights between two fine-tunes, one toward the pro-value and one toward the anti-value responses (<a href="https://proceedings.iclr.cc/paper_files/paper/2026/file/df59090e951681e0f98d40f131c4b628-Paper-Conference.pdf">Fierro &amp; Roger, 2026</a>).',
    sentence_emb: 'Sentence embedding (<a href="https://huggingface.co/sentence-transformers/all-mpnet-base-v2">all-mpnet-base-v2</a>) of each value\'s text description, as in past work (<a href="https://arxiv.org/abs/2504.15236">Huang et al., 2025</a>).',
  };
</script>

<section class="chapter" id="predictors">
  <div class="prose">
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
      activation-based methods reach ρ = 0.46. Pick a representation below to compare its similarity matrix with
      the real one, and <strong>click a cell</strong> to compare all five on that pair.
    </p>
  </div>

  <div class="figure">
    {#if board}
      <div class="board card">
        <div class="board-head ui">
          <span class="ctl-label" style="margin:0">Spearman ρ with G · {MODEL_LABEL[model]} {METHOD_LABEL[method]}</span>
          <span class="legend-inline"><span class="tick"></span> mean over 4 settings <span class="ceil"></span> ceiling</span>
        </div>
        <svg viewBox="0 0 {BW} {bars.length * BH + 26}" width="100%" role="img" aria-label="Predictor correlations">
          {#each [0, 0.2, 0.4, 0.6, 0.8, 1] as t}
            <line x1={xs(t)} x2={xs(t)} y1="0" y2={bars.length * BH} stroke="#e1e0d9" />
            <text x={xs(t)} y={bars.length * BH + 16} text-anchor="middle" class="axis num">{t.toFixed(1)}</text>
          {/each}
          {#each bars as b, r}
            <g transform="translate(0,{r * BH})" opacity={b.id === pred ? 1 : 0.55}>
              <text x={LX - 10} y={BH / 2 + 4} text-anchor="end" class="blabel" font-weight={b.id === pred ? 600 : 400}>{label(b.id)}</text>
              <rect x={xs(0)} y={BH / 2 - 7} width={Math.max(0, xs(b.rho) - xs(0))} height="14" rx="3" fill={PRED_HEX[b.id]} />
              <line x1={xs(b.ci[0])} x2={xs(b.ci[1])} y1={BH / 2} y2={BH / 2} stroke="#0b0b0b" stroke-width="1.25" />
              <line x1={xs(b.agg)} x2={xs(b.agg)} y1={BH / 2 - 10} y2={BH / 2 + 10} stroke="#0b0b0b" stroke-width="2" />
              <text x={Math.max(xs(b.rho), xs(b.ci[1])) + 8} y={BH / 2 + 4} class="bval num">{b.rho.toFixed(2)}</text>
            </g>
          {/each}
          <line x1={xs(board.ceiling[arm])} x2={xs(board.ceiling[arm])} y1="-2" y2={bars.length * BH} stroke="#898781" stroke-dasharray="4 3" />
          <text x={xs(board.ceiling[arm]) - 4} y="10" text-anchor="end" class="axis">ceiling {board.ceiling[arm].toFixed(2)}</text>
        </svg>
      </div>
    {/if}
    <div class="rail ui tgrid">
      <div class="toolbar-row"><Controls bind:model bind:method /></div>
      {#if board}
        <div class="ctl">
          <span class="ctl-label">Representation</span>
          <div class="predlist" role="group" aria-label="Representation">
            {#each predIds as p}
              <button class="predbtn" aria-pressed={pred === p} onclick={() => (pred = p)}>
                <span class="sw" style="background:{PRED_HEX[p]}"></span>{label(p)}
                <span class="num share">ρ {board.rho[arm][p].toFixed(2)}</span>
              </button>
            {/each}
          </div>
        </div>
      {:else}<div></div>{/if}
      <div class="ctl ui">
        <span class="ctl-label">Rank among all pairs</span>
        <div class="legbar" style="background: linear-gradient(90deg, {legendStops.map((s) => rankColor(s)).join(',')})"></div>
        <div class="legticks num"><span>lowest</span><span>highest</span></div>
      </div>
      {#if board}<p class="pdesc ink2">{@html PRED_DESC[pred]}</p>{/if}
    </div>

    {#if P && values.length && board}
      <div class="pair" bind:clientWidth={pairW}>
        <div class="mcol">
          <div class="mtitle ui" style="padding-left:{ROWG}px">Real effect <strong>G</strong></div>
          <Matrix rows={rowLabels} cols={colLabels} color={colorG} {diag} selected={sel} colDivider={49}
            {onselect} {onhover} hoverExt={hover} showColLabels={false} rowGutter={ROWG} {cellSize}
            ariaLabel="Generalization matrix G, ranked" />
        </div>
        <div class="mcol">
          <div class="mtitle ui"><span class="sw" style="background:{PRED_HEX[pred]}"></span><strong>{label(pred)}</strong> similarity · ρ = {board.rho[arm][pred].toFixed(2)}</div>
          <Matrix rows={rowLabels} cols={colLabels} color={colorP} {diag} selected={sel} colDivider={49}
            {onselect} {onhover} hoverExt={hover} showColLabels={false} showRowLabels={false} {cellSize}
            ariaLabel={`${label(pred)} similarity matrix, ranked`} />
        </div>
      </div>
    {/if}

    <div class="below">
      <aside class="detail card ui">
        {#if cell && values.length}
          <h3 class="headline"><span class="v">{values[cell.v1].name}</span> → <span class="v">{values[cell.v2].name}</span></h3>
          {#if cell.self}
            <p class="ink2">Same value on both axes: not a transfer pair, so predictors aren't scored here.</p>
          {:else}
            <div class="dgrid">
              <div>
                <p class="ink2">The real effect ranks in the <strong>{ord(cell.g)} percentile</strong> of all pairs (black line). Dots show where each representation ranks this pair.</p>
                <svg viewBox="0 0 360 {cell.ranked.length * 26 + 30}" width="100%" style="max-width:400px" role="img" aria-label="Percentile comparison">
                  {#each [0, 25, 50, 75, 100] as t}
                    <text x={130 + t * 2.1} y={cell.ranked.length * 26 + 22} text-anchor="middle" class="axis num">{t}</text>
                  {/each}
                  <line x1={130 + cell.g * 2.1} x2={130 + cell.g * 2.1} y1="0" y2={cell.ranked.length * 26 + 6} stroke="#0b0b0b" stroke-width="1.5" />
                  {#each cell.ranked as r, n}
                    <g transform="translate(0,{n * 26 + 14})">
                      <text x="120" y="4" text-anchor="end" class="blabel" font-weight={r.id === pred ? 600 : 400}>{label(r.id)}</text>
                      <line x1="130" x2="340" y1="0" y2="0" stroke="#e1e0d9" />
                      <line x1={130 + cell.g * 2.1} x2={130 + r.pct * 2.1} y1="0" y2="0" stroke={PRED_HEX[r.id]} stroke-opacity="0.45" stroke-width="3" stroke-linecap="round" />
                      <circle cx={130 + r.pct * 2.1} cy="0" r="5.5" fill={PRED_HEX[r.id]} stroke="#fcfcfb" stroke-width="2" />
                    </g>
                  {/each}
                </svg>
              </div>
              <table class="rank num">
                <thead><tr><th></th><th>Representation</th><th>cos</th><th>pct</th><th>off by</th></tr></thead>
                <tbody>
                  {#each cell.ranked as r}
                    <tr class:cur={r.id === pred}>
                      <td><span class="sw" style="background:{PRED_HEX[r.id]}"></span></td>
                      <td>{label(r.id)}</td><td>{r.cos?.toFixed(2)}</td><td>{r.pct}</td><td>{r.resid}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
              <div class="sc">
                <span class="ctl-label">This pair among all pairs</span>
                <canvas bind:this={scatter}></canvas>
              </div>
            </div>
          {/if}
        {:else}
          <p class="ink2">Click a cell to compare predictors.</p>
        {/if}
      </aside>

    </div>
  </div>

  {#if tip && values.length}
    <div class="tooltip num" style="left:{tip.x + 14}px; top:{tip.y + 14}px">
      <strong>{values[tip.v1].name}</strong> → {values[tip.v2].name}<br />
      {#if tip.g == null}Same value{:else}G rank {tip.g} · {label(pred)} rank {tip.p}{/if}
    </div>
  {/if}
</section>

<style>
  .rail { margin-bottom: 18px; }
  .tgrid { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 4px 28px; align-items: end; }
  .tgrid .ctl { margin-bottom: 0; }
  .legbar { width: 180px; height: 10px; border-radius: 3px; }
  .legticks { display: flex; justify-content: space-between; font-size: 11px; color: var(--ink-2); width: 180px; }
  .pair { display: flex; gap: 28px; align-items: flex-start; overflow-x: auto; }
  .mcol { flex: none; }
  .mtitle { font-size: 13px; margin-bottom: 6px; display: flex; align-items: center; gap: 6px; }
  .below { margin-top: 24px; }
  .board { padding: 14px 16px 8px; max-width: 600px; margin-bottom: 24px; }
  .pdesc { max-width: 620px; font-size: 13px; margin: 0; padding-bottom: 2px; align-self: center; }
  .board-head { display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 8px; margin-bottom: 6px; }
  .legend-inline { font-size: 11px; color: var(--ink-2); display: inline-flex; align-items: center; gap: 6px; }
  .legend-inline .tick { display: inline-block; width: 2px; height: 12px; background: var(--ink); }
  .legend-inline .ceil { display: inline-block; width: 0; height: 12px; border-left: 1px dashed var(--muted); margin-left: 6px; }
  svg .axis { font: 10px Inter, sans-serif; fill: #52514e; }
  svg .blabel { font: 12px Inter, sans-serif; fill: #0b0b0b; }
  svg .bval { font: 600 12px Inter, sans-serif; fill: #0b0b0b; }
  .predlist { display: flex; flex-wrap: wrap; gap: 4px; }
  .predbtn { display: inline-flex; align-items: center; gap: 7px; border: 1px solid var(--border); background: var(--surface); border-radius: 999px; padding: 4px 10px; cursor: pointer; font-family: var(--sans); font-size: 13px; color: var(--ink); }
  .predbtn:hover { background: var(--surface-2); }
  .predbtn[aria-pressed='true'] { border-color: var(--ink); box-shadow: 0 0 0 1px var(--ink); font-weight: 600; }
  .share { color: var(--ink-2); font-size: 12px; font-weight: 400; }
  .sw { display: inline-block; width: 10px; height: 10px; border-radius: 3px; flex: none; }
  .detail { padding: 18px; }
  .dgrid { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr) auto; gap: 12px 28px; align-items: start; }
  .headline { font-size: 16px; font-weight: 500; margin: 0 0 8px; }
  .headline .v { font-weight: 700; }
  .detail p { font-size: 13px; margin: 0 0 8px; }
  .rank { width: 100%; border-collapse: collapse; font-size: 12.5px; }
  .rank th { text-align: left; font-weight: 600; color: var(--ink-2); font-size: 11px; border-bottom: 1px solid var(--grid); padding: 4px; }
  .rank td { padding: 4px; border-bottom: 1px solid var(--grid); }
  .rank tr.cur td { font-weight: 600; }
  .sc canvas { display: block; margin-top: 6px; }
  @media (max-width: 1180px) {
    .tgrid { grid-template-columns: minmax(0, 1fr); }
    .dgrid { grid-template-columns: minmax(0, 1fr); }
  }
</style>
