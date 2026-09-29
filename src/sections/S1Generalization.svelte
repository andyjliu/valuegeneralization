<script>
  import Matrix from '../lib/Matrix.svelte';
  import Controls from '../lib/Controls.svelte';
  import DivLegend from '../lib/DivLegend.svelte';
  import FlipCard from '../lib/FlipCard.svelte';
  import { load, armId, divColor, fmtPct, MODEL_LABEL, METHOD_LABEL } from '../lib/data.js';

  let model = $state('qwen');
  let method = $state('dpo');
  let order = $state('paper');
  let values = $state([]);
  let G = $state(null);
  let sel = $state(null);            // {v1, v2} value indices (survives arm switches)
  let tip = $state(null);
  let flips = $state(null);
  let exIdx = $state(0);

  let arm = $derived(armId(model, method));
  load('values.json').then((v) => (values = v));
  $effect(() => {
    const a = arm;
    load(`g_${a}.json`).then((g) => { if (a === arm) G = g; });
  });

  const nC = $derived(G ? G.cols.length : 0);
  const gAt = (ri, cj) => G.g[ri * nC + cj] / 1000;
  // row permutation
  let rowOrder = $derived.by(() => {
    if (!G) return [];
    const idx = G.rows.map((_, i) => i);
    if (order === 'mean') {
      const m = idx.map((i) => {
        let s = 0;
        for (let j = 0; j < nC; j++) if (G.cols[j] !== G.rows[i]) s += gAt(i, j);
        return s / (nC - 1);
      });
      idx.sort((a, b) => m[b] - m[a]);
    }
    return idx;
  });
  let rowLabels = $derived(values.length && G ? rowOrder.map((i) => values[G.rows[i]].name) : []);
  let colLabels = $derived(values.length && G ? G.cols.map((c) => values[c].name) : []);
  let color = $derived(G ? (i, j) => divColor(gAt(rowOrder[i], j)) : () => '#eee');
  let diag = $derived(G ? (i, j) => G.rows[rowOrder[i]] === G.cols[j] : () => false);

  // selection <-> matrix coords
  let selCell = $derived.by(() => {
    if (!G || !sel) return null;
    const ri = G.rows.indexOf(sel.v1), j = G.cols.indexOf(sel.v2);
    if (ri < 0 || j < 0) return null;
    return { i: rowOrder.indexOf(ri), j, ri };
  });

  function onselect(c) {
    if (!c) { sel = null; return; }
    sel = { v1: G.rows[rowOrder[c.i]], v2: G.cols[c.j] };
    exIdx = 0;
  }
  function onhover(c, ev) {
    tip = c && G ? { x: ev.clientX, y: ev.clientY, v1: G.rows[rowOrder[c.i]], v2: G.cols[c.j], g: gAt(rowOrder[c.i], c.j) } : null;
  }

  $effect(() => {
    flips = null;
    const c = selCell, a = arm;
    if (!c) return;
    load(`flips/${a}/${c.ri}.json`).then((f) => { if (a === arm) flips = f; });
  });

  // default selection: a striking off-diagonal cell once data arrives
  $effect(() => {
    if (G && values.length && !sel) {
      let best = null;
      for (let i = 0; i < G.rows.length; i++)
        for (let j = 0; j < nC; j++)
          if (G.rows[i] !== G.cols[j] && (!best || gAt(i, j) > best.g)) best = { i, j, g: gAt(i, j) };
      sel = { v1: G.rows[best.i], v2: G.cols[best.j] };
    }
  });

  let cellInfo = $derived.by(() => {
    if (!selCell || !G) return null;
    const k = selCell.ri * nC + selCell.j;
    return { g: G.g[k] / 1000, n: G.n[k], toward: G.toward[k], away: G.away[k] };
  });
  let exs = $derived(flips && selCell ? flips.cells[selCell.j] : []);
  let modelLabel = $derived(MODEL_LABEL[model]);

  function headline(g) {
    const v1 = values[sel.v1].name, v2 = values[sel.v2].name;
    if (Math.abs(g) < 0.05) return { pre: `Training on`, v1, verb: `barely moves ${modelLabel} on`, v2, pct: null };
    return { pre: 'Training on', v1, verb: `steers ${modelLabel}`, pct: fmtPct(g), dir: g > 0 ? 'toward' : 'away from', v2 };
  }
</script>

<section class="chapter" id="generalization">
  <div class="prose">
    <div class="eyebrow">Part 1</div>
    <h2>Introducing value alignment generalization</h2>
    <p>
      LLM developers post-train their models to exhibit prosocial values, but training on narrow behaviors can
      influence model behavior in unexpected ways. We aim to empirically predict <em>alignment generalization</em>:
      how training a model to follow one value influences its propensity to follow values that it was not trained
      on. We train models to follow individual values from a set of 66 values drawn from Anthropic's constitution,
      then evaluate how this shifts their adherence to all the others. We do this with two training methods,
      single-value DPO and single-value SFT, on two base models (Olmo-3-7B and Qwen-3-8B-Base), giving a
      <em>generalization matrix</em> G where G(v₁, v₂) denotes how well training on value v₁ transfers to value v₂.
    </p>
    <p>
      We measure adherence with ConflictScope: 11,731 scenarios in which two values recommend different actions,
      with an LLM judge scoring how v₂-aligned the model's action was. G(v₁, v₂) is the proportion of the
      remaining alignment gap toward v₂ that is closed by fine-tuning on v₁. A score of −1 means the fine-tuned
      model never aligns with v₂, while 0.5 is equivalent to flipping the model toward v₂ in half of the cases
      where the base model was misaligned with it. <strong>Click any cell</strong> to see a scenario where the
      model's choice flipped.
    </p>
  </div>

  <div class="figure">
    <div class="layout">
      <div class="rail ui toolbar-row">
        <Controls bind:model bind:method>
          <div class="ctl">
            <span class="ctl-label">Row order</span>
            <div class="seg" role="group" aria-label="Row order">
              <button aria-pressed={order === 'paper'} onclick={() => (order = 'paper')}>Paper</button>
              <button aria-pressed={order === 'mean'} onclick={() => (order = 'mean')}>By mean effect</button>
            </div>
          </div>
        </Controls>
        <DivLegend />
        <p class="note muted">
          Outlined cells: training and evaluating on the same value.
          {#if method === 'sft'}Rows below the dashed line are the 17 values we could only train with SFT.{/if}
        </p>
      </div>

      <div class="main">
        {#if G && values.length}
          <Matrix
            rows={rowLabels}
            cols={colLabels}
            {color}
            {diag}
            selected={selCell}
            rowDivider={method === 'sft' && order === 'paper' ? 49 : null}
            colDivider={49}
            {onselect}
            {onhover}
            ariaLabel={`Generalization matrix for ${modelLabel} ${METHOD_LABEL[method]}`}
          />
        {:else}
          <div class="ui muted" style="padding:40px">Loading matrix…</div>
        {/if}
      </div>

      <aside class="detail card">
        {#if sel && cellInfo && values.length}
          {@const h = headline(cellInfo.g)}
          <h3 class="headline">
            {h.pre} <span class="v">{h.v1}</span> {h.verb}
            {#if h.pct}<span class="big" style="color:{cellInfo.g > 0 ? 'var(--div-pos)' : 'var(--div-neg)'}">{h.pct} {h.dir}</span>{/if}
            <span class="v">{h.v2}</span>
          </h3>
          <p class="stats ui ink2 num">
            G = {cellInfo.g >= 0 ? '+' : ''}{cellInfo.g.toFixed(2)} · across {cellInfo.n} scenarios involving this value,
            {cellInfo.toward} flipped toward it and {cellInfo.away} away.
          </p>
          <details class="descs ui">
            <summary>What these values mean</summary>
            <p><strong>{values[sel.v1].name}:</strong> {values[sel.v1].desc}</p>
            <p><strong>{values[sel.v2].name}:</strong> {values[sel.v2].desc}</p>
          </details>
          {#if exs.length}
            <div class="pager ui">
              <span class="eyebrow">Example {exIdx + 1} of {exs.length}</span>
              <span>
                <button class="btn" disabled={exIdx === 0} onclick={() => exIdx--} aria-label="Previous example">‹</button>
                <button class="btn" disabled={exIdx >= exs.length - 1} onclick={() => exIdx++} aria-label="Next example">›</button>
              </span>
            </div>
            <FlipCard ex={exs[exIdx]} {arm} {values} v2={sel.v2} {modelLabel} />
          {:else if flips}
            <p class="ui muted">No scenario flipped in this direction.</p>
          {:else}
            <p class="ui muted">Loading examples…</p>
          {/if}
        {:else if sel && G && G.rows.indexOf(sel.v1) < 0}
          <p class="ui muted">“{values[sel.v1]?.name}” was only trained with SFT. Pick another cell.</p>
        {:else}
          <p class="ui muted">Click a cell to inspect it.</p>
        {/if}
      </aside>
    </div>
  </div>

  {#if tip}
    <div class="tooltip num" style="left:{tip.x + 14}px; top:{tip.y + 14}px">
      <strong>{values[tip.v1].name}</strong> → {values[tip.v2].name}<br />G = {tip.g >= 0 ? '+' : ''}{tip.g.toFixed(2)}
    </div>
  {/if}
</section>

<style>
  .layout { display: grid; grid-template-columns: minmax(0, 1fr) 380px; gap: 24px; align-items: start; }
  .rail { grid-column: 1 / -1; }
    .note { font-size: 12px; margin: 0; max-width: 260px; }
  .detail { position: sticky; top: calc(var(--header-h) + 20px); padding: 18px; max-height: calc(100vh - var(--header-h) - 40px); overflow-y: auto; }
  .headline { font-size: 17px; font-weight: 500; line-height: 1.35; margin: 0 0 8px; }
  .headline .v { font-weight: 700; }
  .headline .big { font-weight: 700; }
  .stats { font-size: 12.5px; margin: 0 0 10px; }
  .descs { font-size: 12.5px; margin-bottom: 12px; color: var(--ink-2); }
  .descs summary { cursor: pointer; color: var(--accent); }
  .descs p { margin: 6px 0; }
  .pager { display: flex; justify-content: space-between; align-items: center; margin: 8px 0 8px; }
  .pager .btn { padding: 2px 10px; }
  .pager .btn:disabled { opacity: 0.4; cursor: default; }
  @media (max-width: 1180px) {
    .layout { grid-template-columns: minmax(0, 1fr); }
        .detail { position: static; max-height: none; }
  }
</style>
