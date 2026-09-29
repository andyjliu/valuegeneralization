<script>
  import { interpolateLab } from 'd3-interpolate';
  import { load } from '../lib/data.js';

  const KMAX = 15;
  let values = $state([]);
  let mv = $state(null);
  let target = $state([]);
  let emb = $state('persona');
  let query = $state('');
  let overDrop = $state(false);
  let shake = $state(false);
  let hoverPair = $state(null);
  let dragging = $state(null);   // {i, from: 'palette'|'target'}

  load('values.json').then((v) => (values = v));
  load('multivalue.json').then((d) => {
    mv = d;
    const best = [...d.presets].sort((a, b) => b.coh - a.coh)[0];
    target = [...best.values];
  });

  let M = $derived(mv ? mv.cos[emb] : null);
  const coherenceOf = (ids) => {
    if (ids.length < 2) return null;
    let s = 0, n = 0;
    for (let a = 0; a < ids.length; a++) for (let b = a + 1; b < ids.length; b++) { s += M[ids[a]][ids[b]]; n++; }
    return s / n;
  };
  let coh = $derived(M ? coherenceOf(target) : null);
  let q = $derived(mv && target.length >= 2 ? mv.quantiles[emb][target.length] : null);
  let pct = $derived.by(() => {
    if (coh == null || !q) return null;
    if (coh <= q[0]) return 0;
    if (coh >= q[100]) return 100;
    let i = 0;
    while (q[i + 1] < coh) i++;
    return i + (coh - q[i]) / Math.max(1e-9, q[i + 1] - q[i]);
  });
  let pairs = $derived.by(() => {
    if (!M || target.length < 2) return [];
    const out = [];
    for (let a = 0; a < target.length; a++) for (let b = a + 1; b < target.length; b++) out.push({ a: target[a], b: target[b], cos: M[target[a]][target[b]] });
    return out.sort((x, y) => y.cos - x.cos);
  });
  let loo = $derived(target.length >= 3 && coh != null ? target.map((v) => coherenceOf(target.filter((t) => t !== v)) - coh) : target.map(() => null));
  let oddOne = $derived(loo.length && loo[0] != null ? target[loo.indexOf(Math.max(...loo))] : null);

  // cosine range for the pair heatmap colour scale (1st-99th pct of all off-diagonal pairs)
  let range = $derived.by(() => {
    if (!M) return [0, 1];
    const xs = [];
    for (let a = 0; a < 66; a++) for (let b = a + 1; b < 66; b++) xs.push(M[a][b]);
    xs.sort((x, y) => x - y);
    return [xs[Math.floor(xs.length * 0.01)], xs[Math.floor(xs.length * 0.99)]];
  });
  const seq = interpolateLab('#eef3fb', '#104281');
  const pairColor = (c) => seq(Math.max(0, Math.min(1, (c - range[0]) / (range[1] - range[0]))));

  function add(i) {
    if (target.includes(i)) return;
    if (target.length >= KMAX) { shake = true; setTimeout(() => (shake = false), 450); return; }
    target = [...target, i];
  }
  const remove = (i) => (target = target.filter((t) => t !== i));
  function randomK(k = 6) {
    const pool = values.map((_, i) => i);
    for (let i = pool.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [pool[i], pool[j]] = [pool[j], pool[i]]; }
    target = pool.slice(0, k);
  }
  function preset(which) {
    const s = [...mv.presets].sort((a, b) => a.coh - b.coh);
    target = [...(which === 'high' ? s[s.length - 1] : s[0]).values];
  }

  let filtered = $derived(values.map((v, i) => ({ v, i })).filter(({ v }) => !query || v.name.toLowerCase().includes(query.toLowerCase())));
  let groups = $derived([
    { title: 'Trained values', items: filtered.filter(({ v }) => v.trained) },
    { title: 'SFT-only values', items: filtered.filter(({ v }) => !v.trained) },
  ]);

  // distribution strip geometry
  const SW = 360, SH = 70;
  let strip = $derived.by(() => {
    if (!q) return null;
    const lo = q[1], hi = q[99];
    const x0 = Math.min(lo, coh ?? lo), x1 = Math.max(hi, coh ?? hi);
    const padX = (x1 - x0) * 0.06;
    const X = (v) => 8 + ((v - (x0 - padX)) / (x1 - x0 + 2 * padX)) * (SW - 16);
    const dens = [];
    for (let i = 1; i < 99; i++) dens.push({ x: (q[i] + q[i + 1]) / 2, d: 1 / Math.max(1e-6, q[i + 1] - q[i]) });
    const dmax = Math.max(...dens.map((d) => d.d));
    const Y = (d) => SH - 18 - (d / dmax) * (SH - 26);
    const area = `M${X(dens[0].x)},${SH - 18} ` + dens.map((d) => `L${X(d.x)},${Y(d.d)}`).join(' ') + ` L${X(dens.at(-1).x)},${SH - 18} Z`;
    return { X, area, lo, hi, ticks: [q[5], q[50], q[95]] };
  });
  const ord = (n) => { const s = ['th', 'st', 'nd', 'rd'], v = n % 100; return n + (s[(v - 20) % 10] || s[v] || s[0]); };
</script>

<section class="chapter" id="multivalue">
  <div class="prose">
    <h2>Build your own alignment target</h2>
    <p>
      Real <a href="https://arxiv.org/abs/2404.10636">alignment targets</a> list many values at once. We hypothesize that models trained on more coherent sets of
      traits adhere to their alignment target more robustly. For a multi-value alignment target T = {'{'}v₁, …, vₙ{'}'}
      and a value embedding E, we define the <em>coherence</em> of T as the average pairwise cosine similarity of the
      embeddings of its values.
    </p>
    <p>
      We trained Qwen-3-8B on 64 six-value targets and measured prefill robustness: whether the model keeps
      following its target after anti-target text is injected into its context. Persona-derived coherence is
      significantly correlated with robustness (ρ = 0.43, p = 5×10⁻⁴), while description-derived coherence is not
      (ρ = 0.12, p = 0.37). <strong>Drag values into the target</strong> to see how coherent your set is, and which
      pairs pull it together or apart.
    </p>
  </div>

  <div class="figure">
    <div class="layout ui">
      <aside class="palette card">
        <input type="search" placeholder="Search 66 values…" bind:value={query} aria-label="Search values" />
        <div class="plist"
          ondragover={(e) => { if (dragging?.from === 'target') e.preventDefault(); }}
          ondrop={(e) => { e.preventDefault(); if (dragging?.from === 'target') remove(dragging.i); dragging = null; }}
          role="list">
          {#each groups as g}
            {#if g.items.length}
              <div class="ghead eyebrow">{g.title} <span class="num">{g.items.length}</span></div>
              {#each g.items as { v, i }}
                <button class="chip" class:used={target.includes(i)} draggable={!target.includes(i)}
                  ondragstart={() => (dragging = { i, from: 'palette' })} ondragend={() => (dragging = null)}
                  onclick={() => (target.includes(i) ? remove(i) : add(i))} title={v.desc}
                  aria-label={`${target.includes(i) ? 'Remove' : 'Add'} ${v.name}`}>
                  {v.name}
                </button>
              {/each}
            {/if}
          {/each}
        </div>
      </aside>

      <div class="center">
        <div class="toolbar">
          <button class="btn" onclick={() => randomK(6)}>Random 6</button>
          <button class="btn" onclick={() => preset('high')} disabled={!mv}>Most coherent paper target</button>
          <button class="btn" onclick={() => preset('low')} disabled={!mv}>Least coherent paper target</button>
          <button class="btn" onclick={() => (target = [])}>Clear</button>
        </div>
        <div class="drop card" class:over={overDrop} class:shake
          ondragover={(e) => { e.preventDefault(); overDrop = true; }}
          ondragleave={() => (overDrop = false)}
          ondrop={(e) => { e.preventDefault(); overDrop = false; if (dragging?.from === 'palette') add(dragging.i); dragging = null; }}
          role="list" aria-label="Alignment target">
          <div class="drop-head">
            <span class="eyebrow">Your alignment target</span>
            <span class="num muted">{target.length} / {KMAX}{shake ? ' · 15 max' : ''}</span>
          </div>
          {#if !target.length}
            <div class="empty muted">Drag values here, or click them in the list (2–{KMAX} values).</div>
          {/if}
          <div class="tchips">
            {#each target as t, n}
              <div class="tchip" role="listitem" draggable="true"
                class:hl={hoverPair && (hoverPair.a === t || hoverPair.b === t)}
                class:odd={oddOne === t}
                ondragstart={() => (dragging = { i: t, from: 'target' })} ondragend={() => (dragging = null)}>
                <span class="tname" title={values[t]?.desc}>{values[t]?.name}</span>
                {#if loo[n] != null}
                  <span class="loo num" title="Change in coherence if removed">
                    <span class="loobar" style="width:{Math.min(40, Math.abs(loo[n]) * 400)}px; background:{loo[n] > 0 ? '#b8312f' : '#1c5cab'}"></span>
                    {loo[n] > 0 ? '+' : '−'}{Math.abs(loo[n]).toFixed(3)}
                  </span>
                {/if}
                <button class="x" onclick={() => remove(t)} aria-label={`Remove ${values[t]?.name}`}>×</button>
              </div>
            {/each}
          </div>
        </div>

        {#if pairs.length}
          <div class="pairs card">
            <div class="pcol">
              <div class="eyebrow">Most similar pairs</div>
              {#each pairs.slice(0, 3) as p}
                <div class="prow" role="listitem" onmouseenter={() => (hoverPair = p)} onmouseleave={() => (hoverPair = null)}>
                  <span class="sw" style="background:{pairColor(p.cos)}"></span>
                  <span>{values[p.a].name} <span class="muted">&amp;</span> {values[p.b].name}</span>
                  <span class="num">{p.cos.toFixed(2)}</span>
                </div>
              {/each}
            </div>
            <div class="pcol">
              <div class="eyebrow">Least similar pairs</div>
              {#each pairs.slice(-3).reverse() as p}
                <div class="prow" role="listitem" onmouseenter={() => (hoverPair = p)} onmouseleave={() => (hoverPair = null)}>
                  <span class="sw" style="background:{pairColor(p.cos)}"></span>
                  <span>{values[p.a].name} <span class="muted">&amp;</span> {values[p.b].name}</span>
                  <span class="num">{p.cos.toFixed(2)}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>

      <aside class="readout card">
        <div class="ctl">
          <span class="ctl-label">Embedding</span>
          <div class="seg" role="group" aria-label="Embedding">
            <button aria-pressed={emb === 'persona'} onclick={() => (emb = 'persona')}>Persona</button>
            <button aria-pressed={emb === 'description'} onclick={() => (emb = 'description')}>Description-Embd</button>
          </div>
        </div>
        {#if coh == null}
          <div class="big muted">—</div>
          <p class="muted">Add at least two values.</p>
        {:else}
          <div class="eyebrow">Coherence</div>
          <div class="big num">{coh.toFixed(3)}</div>
          <p class="pctline">More coherent than <strong class="num">{Math.round(pct)}%</strong> of random {target.length}-value targets.</p>
          {#if strip}
            <svg viewBox="0 0 {SW} {SH}" width="100%" role="img" aria-label={`Coherence is at the ${ord(Math.round(pct))} percentile`}>
              <path d={strip.area} fill="#2a78d6" fill-opacity="0.16" stroke="#2a78d6" stroke-width="1.25" />
              <line x1="8" x2={SW - 8} y1={SH - 18} y2={SH - 18} stroke="#c3c2b7" />
              {#each strip.ticks as t, n}
                <text x={strip.X(t)} y={SH - 4} text-anchor="middle" class="axis num">{['5th', 'median', '95th'][n]}</text>
              {/each}
              <line x1={strip.X(coh)} x2={strip.X(coh)} y1="4" y2={SH - 18} stroke="#0b0b0b" stroke-width="2" />
              <circle cx={strip.X(coh)} cy="6" r="4" fill="#0b0b0b" />
            </svg>
          {/if}
          {#if target.length >= 2}
            <div class="eyebrow" style="margin-top:14px">All pairs</div>
            <svg viewBox="0 0 {target.length * 18 + 4} {target.length * 18 + 4}" width={Math.min(300, target.length * 18 + 4)} role="img" aria-label="Pairwise similarity triangle">
              {#each target as a, r}
                {#each target as b, c}
                  {#if c < r}
                    <rect x={c * 18 + 2} y={r * 18 + 2} width="16" height="16" rx="2" fill={pairColor(M[a][b])}
                      stroke={hoverPair && ((hoverPair.a === a && hoverPair.b === b) || (hoverPair.a === b && hoverPair.b === a)) ? '#0b0b0b' : 'none'} stroke-width="2"
                      role="presentation"
                      onmouseenter={() => (hoverPair = { a, b, cos: M[a][b] })} onmouseleave={() => (hoverPair = null)} />
                  {/if}
                {/each}
              {/each}
            </svg>
            {#if hoverPair}<p class="small ink2">{values[hoverPair.a].name} &amp; {values[hoverPair.b].name}: cos {hoverPair.cos.toFixed(2)}</p>{/if}
          {/if}
        {/if}
      </aside>
    </div>
  </div>
</section>

<style>
  .layout { display: grid; grid-template-columns: 280px minmax(0, 1fr) 360px; gap: 20px; align-items: start; }
  .palette { padding: 12px; position: sticky; top: calc(var(--header-h) + 20px); max-height: calc(100vh - var(--header-h) - 40px); display: flex; flex-direction: column; }
  .palette input { border: 1px solid var(--border); border-radius: 8px; padding: 6px 10px; margin-bottom: 8px; background: var(--surface); }
  .plist { overflow-y: auto; display: flex; flex-direction: column; gap: 3px; }
  .ghead { margin: 8px 0 4px; }
  .chip { text-align: left; border: 1px solid var(--border); background: var(--surface); border-radius: 8px; padding: 5px 9px; cursor: grab; font-size: 12.5px; color: var(--ink); }
  .chip:hover { border-color: var(--accent); }
  .chip.used { opacity: 0.4; cursor: pointer; text-decoration: line-through; }
  .center { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
  .toolbar { display: flex; flex-wrap: wrap; gap: 8px; }
  .toolbar .btn:disabled { opacity: .5; }
  .drop { padding: 14px; min-height: 180px; border: 2px dashed var(--axis); transition: border-color .15s, background .15s; }
  .drop.over { border-color: var(--accent); background: var(--accent-soft); }
  .drop.shake { animation: shake .4s; }
  @keyframes shake { 20%, 60% { transform: translateX(-5px); } 40%, 80% { transform: translateX(5px); } }
  @media (prefers-reduced-motion: reduce) { .drop.shake { animation: none; border-color: #b8312f; } }
  .drop-head { display: flex; justify-content: space-between; margin-bottom: 8px; }
  .empty { padding: 30px 0; text-align: center; }
  .tchips { display: flex; flex-wrap: wrap; gap: 8px; }
  .tchip { display: flex; align-items: center; gap: 8px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 6px 6px 6px 10px; font-size: 13px; cursor: grab; }
  .tchip.hl { border-color: var(--ink); box-shadow: 0 0 0 1px var(--ink); }
  .tchip.odd .tname::after { content: 'odd one out'; margin-left: 6px; font-size: 10px; font-weight: 700; color: #b8312f; text-transform: uppercase; letter-spacing: .04em; }
  .loo { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; color: var(--ink-2); }
  .loobar { display: inline-block; height: 6px; border-radius: 2px; }
  .x { border: 0; background: none; font-size: 16px; color: var(--muted); cursor: pointer; padding: 0 4px; }
  .pairs { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 14px; }
  .prow { display: grid; grid-template-columns: 12px 1fr auto; gap: 8px; align-items: center; font-size: 12.5px; padding: 4px 0; border-bottom: 1px solid var(--grid); }
  .sw { width: 12px; height: 12px; border-radius: 3px; }
  .readout { padding: 16px; position: sticky; top: calc(var(--header-h) + 20px); }
  .big { font-size: 44px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1; }
  .pctline { margin: 4px 0 8px; }
  .small { font-size: 11.5px; margin: 4px 0; }
  svg .axis { font: 10px Inter, sans-serif; fill: #898781; }
  @media (max-width: 1180px) {
    .layout { grid-template-columns: minmax(0, 1fr); }
    .palette, .readout { position: static; max-height: 360px; }
    .readout { max-height: none; }
  }
</style>
