<script>
  import { divColor } from './data.js';
  let { label = 'G(v₁, v₂)' } = $props();
  const stops = Array.from({ length: 21 }, (_, k) => -1 + k * 0.1);
</script>

<div class="leg ui">
  <span class="ctl-label" style="margin:0">{label}</span>
  <div class="bar" style="background: linear-gradient(90deg, {stops.map((s) => divColor(s)).join(',')})"></div>
  <div class="ticks num"><span>−1<br /><small>away from v₂</small></span><span>0</span><span style="text-align:right">+1<br /><small>toward v₂</small></span></div>
</div>

<style>
  .leg { width: 220px; }
  .bar { height: 10px; border-radius: 3px; margin: 4px 0 2px; }
  .ticks { display: flex; justify-content: space-between; font-size: 11px; color: var(--ink-2); line-height: 1.2; }
  small { color: var(--muted); font-size: 10px; }
</style>
