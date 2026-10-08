<script>
  import { onMount } from 'svelte';
  import { polygonHull, polygonCentroid } from 'd3-polygon';
  import { line, curveLinearClosed } from 'd3-shape';
  import { zoom, zoomIdentity } from 'd3-zoom';
  import { select } from 'd3-selection';
  import { Delaunay } from 'd3-delaunay';
  import { load, CLUSTER_HEX } from '../lib/data.js';

  let data = $state(null);
  let width = $state(1000);
  let height = $derived(Math.round(Math.max(440, Math.min(760, width * 0.62))));
  const PAD = 48;
  let svg = $state();
  let figEl = $state();
  let transform = $state(zoomIdentity);
  let selected = $state(null);
  let hoverI = $state(null);
  let hidden = $state([false, false, false, false]);
  let query = $state('');
  let tip = $state(null);

  // animated displacement per point
  let disp = $state([]);
  let pointer = null;           // in data-layer (pre-zoom) pixel coords
  let visible = false;
  const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  load('taxonomy.json').then((d) => {
    data = d;
    disp = d.points.map(() => ({ x: 0, y: 0 }));
    selected = d.points.findIndex((p) => p.id === 'diplomatic_communication');
  });

  let ext = $derived.by(() => {
    if (!data) return null;
    const xs = data.points.map((p) => p.x), ys = data.points.map((p) => p.y);
    return { x0: Math.min(...xs), x1: Math.max(...xs), y0: Math.min(...ys), y1: Math.max(...ys) };
  });
  // MDS axes carry no units; dimension 1 is stretched to the width (as in the paper figure)
  const sx = (x) => PAD + ((x - ext.x0) / (ext.x1 - ext.x0)) * (width - 2 * PAD);
  const sy = (y) => PAD + ((ext.y1 - y) / (ext.y1 - ext.y0)) * (height - 2 * PAD);   // y up, as in matplotlib

  let base = $derived(data && ext ? data.points.map((p) => ({ x: sx(p.x), y: sy(p.y) })) : []);
  let pos = $derived(base.map((b, i) => ({ x: b.x + (disp[i]?.x ?? 0), y: b.y + (disp[i]?.y ?? 0) })));

  // central 90% of each cluster (by distance to its centroid in the base layout)
  let cores = $derived.by(() => {
    if (!data || !base.length) return [];
    return [0, 1, 2, 3].map((c) => {
      const idx = data.points.map((p, i) => (p.c === c ? i : -1)).filter((i) => i >= 0);
      const cx = idx.reduce((s, i) => s + base[i].x, 0) / idx.length;
      const cy = idx.reduce((s, i) => s + base[i].y, 0) / idx.length;
      const d = idx.map((i) => Math.hypot(base[i].x - cx, base[i].y - cy));
      const cut = [...d].sort((a, b) => a - b)[Math.floor(0.9 * (d.length - 1))];
      return idx.filter((_, k) => d[k] <= cut);
    });
  });
  const hullLine = line().curve(curveLinearClosed);
  let hulls = $derived(cores.map((core) => {
    const pts = core.map((i) => [pos[i].x, pos[i].y]);
    const h = polygonHull(pts);
    if (!h) return { d: '', c: [0, 0] };
    const c = polygonCentroid(h);
    const padded = h.map(([x, y]) => [c[0] + (x - c[0]) * 1.05, c[1] + (y - c[1]) * 1.05]);
    return { d: hullLine(padded), c };
  }));

  // greedy label placement for the highlighted examples (in unzoomed pixels): try right, left,
  // above, below each point; keep the first spot that overlaps no earlier label or cluster name
  let labelPos = $derived.by(() => {
    if (!data || !base.length) return {};
    const out = {}, boxes = [];
    const CH = 6.4, H = 13;
    // cluster names occupy their centroids
    // (computed from the resting layout so placement doesn't flicker while points drift)
    for (const core of cores) {
      const h = polygonHull(core.map((i) => [base[i].x, base[i].y]));
      if (!h) continue;
      const c = polygonCentroid(h);
      boxes.push({ x0: c[0] - 60, x1: c[0] + 60, y0: c[1] - 20, y1: c[1] + 6 });
    }
    const hit = (b) => boxes.some((q) => b.x0 < q.x1 && b.x1 > q.x0 && b.y0 < q.y1 && b.y1 > q.y0);
    const idx = data.points.map((p, i) => (p.label ? i : -1)).filter((i) => i >= 0);
    for (const i of idx) {
      const { x, y } = base[i], w = data.points[i].name.length * CH;
      const opts = [
        { dx: 8, dy: 3.5, anchor: 'start', b: { x0: x + 6, x1: x + 8 + w, y0: y - 9, y1: y + 4 } },
        { dx: -8, dy: 3.5, anchor: 'end', b: { x0: x - 8 - w, x1: x - 6, y0: y - 9, y1: y + 4 } },
        { dx: 0, dy: -9, anchor: 'middle', b: { x0: x - w / 2, x1: x + w / 2, y0: y - 9 - H, y1: y - 7 } },
        { dx: 0, dy: 17, anchor: 'middle', b: { x0: x - w / 2, x1: x + w / 2, y0: y + 6, y1: y + 6 + H } },
      ];
      const pick = opts.find((o) => o.b.x0 > 4 && o.b.x1 < width - 4 && !hit(o.b)) ?? opts[0];
      boxes.push(pick.b);
      out[i] = { dx: pick.dx, dy: pick.dy, anchor: pick.anchor };
    }
    return out;
  });

  // jiggle loop
  onMount(() => {
    const io = new IntersectionObserver(([e]) => (visible = e.isIntersecting), { threshold: 0.05 });
    io.observe(figEl);
    const zb = zoom().scaleExtent([1, 8]).on('zoom', (e) => (transform = e.transform));
    select(svg).call(zb).on('dblclick.zoom', null);
    resetZoom = () => select(svg).transition().duration(400).call(zb.transform, zoomIdentity);
    let raf, t0 = performance.now();
    const phase = Array.from({ length: 300 }, (_, i) => [Math.sin(i * 12.9898) * 43758.5453 % 6.283, Math.cos(i * 78.233) * 12345.678 % 6.283]);
    function tick(now) {
      raf = requestAnimationFrame(tick);
      if (!visible || !data || reduced || !base.length) return;
      const t = (now - t0) / 1000;
      const w = (2 * Math.PI) / 6;
      const next = disp.map((d, i) => {
        // gentle idle drift; everything settles while a point is hovered so it is easy to click
        const still = hoverI != null;
        let tx = still ? 0 : 0.5 * Math.sin(w * t + phase[i][0]);
        let ty = still ? 0 : 0.5 * Math.cos(w * t * 0.9 + phase[i][1]);
        if (pointer && !still) {
          // points in a ring around the cursor lean away; the ones right under it stay put
          const dx = base[i].x - pointer.x, dy = base[i].y - pointer.y, r = Math.hypot(dx, dy);
          const R0 = 18 / transform.k, R = 60 / transform.k;
          if (r > R0 && r < R) {
            const f = (Math.sin(((r - R0) / (R - R0)) * Math.PI) * 3) / transform.k;
            tx += (dx / r) * f; ty += (dy / r) * f;
          }
        }
        return { x: d.x + (tx - d.x) * 0.15, y: d.y + (ty - d.y) * 0.15 };
      });
      disp = next;
    }
    raf = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(raf); io.disconnect(); };
  });
  let resetZoom = () => {};

  // hover/click snap to the nearest visible point (Voronoi lookup), so dense areas stay clickable
  let delaunay = $derived(base.length ? Delaunay.from(base, (d) => d.x, (d) => d.y) : null);
  function onmove(ev) {
    const r = svg.getBoundingClientRect();
    const [x, y] = transform.invert([ev.clientX - r.left, ev.clientY - r.top]);
    pointer = { x, y };
    let near = null;
    if (delaunay) {
      const i = delaunay.find(x, y);
      if (i >= 0 && !hidden[data.points[i].c] && Math.hypot(base[i].x - x, base[i].y - y) < 12 / transform.k) near = i;
    }
    hoverI = near;
    tip = near == null ? null : { x: ev.clientX, y: ev.clientY, i: near };
  }
  function onclickMap() {
    if (hoverI != null) selected = selected === hoverI ? null : hoverI;
  }
  function onleave() { pointer = null; hoverI = null; tip = null; }

  let nnSet = $derived(selected != null && data ? new Set(data.points[selected].nn.map((n) => n[0])) : new Set());
  let matches = $derived(data && query.trim().length > 1
    ? data.points.map((p, i) => ({ p, i })).filter(({ p }) => p.name.toLowerCase().includes(query.toLowerCase())).slice(0, 8)
    : []);
  function pick(i) { selected = i; query = ''; }
  const opacity = (i) => {
    const p = data.points[i];
    if (hidden[p.c]) return 0.08;
    if (selected == null) return 0.75;
    return i === selected || nnSet.has(i) ? 1 : 0.3;
  };
</script>

<section class="chapter" id="taxonomy">
  <div class="prose">
    <h2>ValueMap: a taxonomy of LLM values</h2>
    <p>
      Where past taxonomies of LLM values clustered value <em>descriptions</em>, we cluster representations that
      better predict how values interact during training. We introduce <strong>ValueMap</strong> and instantiate it on Olmo-3.1-32B-SFT and the 266
      values from <a href="https://arxiv.org/abs/2504.15236"><em>Values in the Wild</em></a>, using k-medoids with k = 4 on persona-vector representations.
    </p>
    <p>
      We identify four clusters: <strong>attunement</strong> values, which relate to supporting healthy
      interpersonal relationships and emotional growth in users; <strong>rigor</strong> values, which support
      rigorous reasoning, objectivity, and excellence in task execution; <strong>stewardship</strong> values,
      supporting the long-term welfare of society and the full consideration of third parties; and
      <strong>integrity</strong> values, supporting professional norms and codes of conduct as well as intellectual
      honesty. We find that this clustering is more predictive of downstream generalization effects than previous
      taxonomies.
    </p>
  </div>

  <div class="figure" bind:this={figEl}>
    <div class="toolbar ui">
      <div class="legend">
        {#if data}
          {#each data.clusters as c, k}
            <button class="chipbtn" aria-pressed={!hidden[k]} onclick={() => (hidden[k] = !hidden[k])} title={c.desc}>
              <span class="dot" style="background:{CLUSTER_HEX[k]}"></span>{c.name} <span class="muted num">{c.n}</span>
            </button>
          {/each}
        {/if}
      </div>
      <div class="search">
        <input type="search" placeholder="Find a value…" bind:value={query} aria-label="Find a value" />
        {#if matches.length}
          <ul class="results card">
            {#each matches as m}
              <li><button onclick={() => pick(m.i)}><span class="dot" style="background:{CLUSTER_HEX[m.p.c]}"></span>{m.p.name}</button></li>
            {/each}
          </ul>
        {/if}
      </div>
      <button class="btn" onclick={() => resetZoom()}>Reset zoom</button>
    </div>

    <div class="mapwrap card" bind:clientWidth={width}>
      <!-- keyboard access to points is via the search box and neighbor list -->
      <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
      <svg bind:this={svg} {width} {height} role="img" aria-label="MDS map of 266 values in four clusters"
        onmousemove={onmove} onmouseleave={onleave} onclick={onclickMap}
        style:cursor={hoverI != null ? 'pointer' : 'grab'}>
        {#if data && base.length}
          <g transform={transform.toString()}>
            {#each hulls as h, k}
              {#if !hidden[k]}
                <path d={h.d} stroke-linejoin="round" fill={CLUSTER_HEX[k]} fill-opacity="0.08" stroke={CLUSTER_HEX[k]} stroke-opacity="0.5" stroke-width={1 / transform.k} />
              {/if}
            {/each}
            {#if selected != null}
              {#each data.points[selected].nn as [j]}
                <line x1={pos[selected].x} y1={pos[selected].y} x2={pos[j].x} y2={pos[j].y} stroke="#0b0b0b" stroke-width={1.25 / transform.k} stroke-opacity="0.6" />
              {/each}
            {/if}
            {#each data.points as p, i}
              <circle
                cx={pos[i].x} cy={pos[i].y}
                r={(i === selected ? 8 : i === hoverI ? 7 : p.medoid ? 6 : 4.5) / Math.sqrt(transform.k)}
                fill={CLUSTER_HEX[p.c]} fill-opacity={opacity(i)}
                stroke={i === selected ? '#0b0b0b' : '#fcfcfb'} stroke-width={(i === selected ? 2 : 1) / transform.k}
                pointer-events="none" data-name={p.name}
              />
            {/each}
            {#each data.points as p, i}
              {#if (p.label || (transform.k > 2.2 && !hidden[p.c])) && !hidden[p.c]}
                {@const o = p.label ? labelPos[i] ?? { dx: 8, dy: 3.5, anchor: 'start' } : { dx: 8, dy: 3.5, anchor: 'start' }}
                <text x={pos[i].x + o.dx / transform.k} y={pos[i].y + o.dy / transform.k} text-anchor={o.anchor} class="plabel" font-size={(p.label ? 11.5 : 10) / transform.k}
                  stroke-width={3 / transform.k} opacity={selected == null || i === selected || nnSet.has(i) ? 1 : 0.45}>{p.name}</text>
              {/if}
            {/each}
            {#each hulls as h, k}
              {#if !hidden[k]}
                <text x={h.c[0]} y={h.c[1]} class="clabel" text-anchor="middle" font-size={22 / transform.k} stroke-width={5 / transform.k}>{data.clusters[k].name}</text>
              {/if}
            {/each}
          </g>
        {/if}
      </svg>

      {#if data && selected != null}
        {@const p = data.points[selected]}
        <div class="vcard card ui">
          <button class="close" onclick={() => (selected = null)} aria-label="Close">×</button>
          <span class="chip" style="--c:{CLUSTER_HEX[p.c]}">{data.clusters[p.c].name}</span>
          <h3>{p.name}</h3>
          <p class="ink2">{p.desc}</p>
          <div class="eyebrow">Nearest neighbors</div>
          <ol class="nn">
            {#each p.nn as [j, cos]}
              <li><button onclick={() => (selected = j)}><span class="dot" style="background:{CLUSTER_HEX[data.points[j].c]}"></span>{data.points[j].name}<span class="num muted">cos {cos.toFixed(2)}</span></button></li>
            {/each}
          </ol>
        </div>
      {/if}
    </div>
    <p class="caption ui ink2">2D non-metric MDS of Olmo-3.1-32B-SFT persona vectors; nearest neighbors use the full-dimensional vectors.</p>
  </div>

  {#if tip && data}
    <div class="tooltip" style="left:{tip.x + 14}px; top:{tip.y + 14}px">{data.points[tip.i].name}</div>
  {/if}
</section>

<style>
  .toolbar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 12px; }
  .legend { display: flex; gap: 6px; flex-wrap: wrap; flex: 1; }
  .chipbtn { display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--border); background: var(--surface); border-radius: 999px; padding: 4px 12px; cursor: pointer; font-size: 13px; font-weight: 600; }
  .chipbtn[aria-pressed='false'] { opacity: 0.45; }
  .dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; flex: none; }
  .search { position: relative; }
  .search input { border: 1px solid var(--border); border-radius: 8px; padding: 6px 10px; width: 220px; background: var(--surface); }
  .results { position: absolute; top: 36px; left: 0; right: 0; z-index: 20; list-style: none; margin: 0; padding: 4px; }
  .results button, .nn button { display: flex; align-items: center; gap: 8px; width: 100%; border: 0; background: none; text-align: left; padding: 5px 6px; border-radius: 6px; cursor: pointer; font: inherit; color: var(--ink); }
  .results button:hover, .nn button:hover { background: var(--surface-2); }
  .mapwrap { position: relative; overflow: hidden; }
  svg { display: block; touch-action: none; }
  .plabel { font-family: Inter, sans-serif; fill: #0b0b0b; paint-order: stroke; stroke: #fcfcfb; stroke-linejoin: round; pointer-events: none; }
  .clabel { font-family: Inter, sans-serif; font-weight: 700; fill: #0b0b0b; paint-order: stroke; stroke: rgba(252,252,251,.85); stroke-linejoin: round; pointer-events: none; letter-spacing: 0.02em; }
  .vcard { position: absolute; top: 14px; right: 14px; width: 300px; padding: 16px; box-shadow: 0 6px 24px rgba(0,0,0,.08); }
  .vcard h3 { margin: 8px 0 6px; font-size: 18px; }
  .vcard p { margin: 0 0 12px; font-size: 13px; }
  .chip { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; }
  .chip::before { content: ''; width: 9px; height: 9px; border-radius: 50%; background: var(--c); }
  .close { position: absolute; top: 8px; right: 10px; border: 0; background: none; font-size: 20px; color: var(--muted); cursor: pointer; }
  .nn { list-style: none; padding: 0; margin: 6px 0 0; }
  .nn .num { margin-left: auto; font-size: 12px; }
  .caption { font-size: 12.5px; max-width: 760px; margin-top: 10px; }
  @media (max-width: 760px) { .vcard { position: static; width: auto; margin: 12px; } }
</style>
