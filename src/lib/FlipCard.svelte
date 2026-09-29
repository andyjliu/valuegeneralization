<script>
  import { load } from './data.js';
  // ex: {s, k, b, f, mock, ft, fj}; arm; values; v2 (value index evaluated on)
  let { ex, arm, values, v2, modelLabel } = $props();

  let scen = $state(null);
  let openPrompt = $state(false);
  $effect(() => {
    scen = null;
    openPrompt = false;
    const e = ex;
    load(`scen/${e.k}.json`).then((b) => { if (e === ex) scen = b[e.s]; });
  });

  let aAligned = $derived(scen ? scen.v1 === v2 : null);
  const name = (i) => values[i]?.name ?? '';
  const scoreColor = (s) => (s >= 0.5 ? '#b8312f' : '#1c5cab');
</script>

{#if !scen}
  <div class="loading ui muted">Loading scenario…</div>
{:else}
  <div class="flip ui">
    <div class="block">
      <div class="eyebrow">ConflictScope scenario</div>
      <div class="prompt" class:clamped={!openPrompt}>
        <span class="role">User</span>{scen.p.trim()}
      </div>
      <button class="link" onclick={() => (openPrompt = !openPrompt)}>{openPrompt ? 'Show less' : 'Show full prompt'}</button>
      <div class="actions">
        <div class="act" class:aligned={aAligned}>
          <span class="tag">Action A · {name(scen.v1)}</span>
          <p>{scen.a1}</p>
        </div>
        <div class="act" class:aligned={!aAligned}>
          <span class="tag">Action B · {name(scen.v2)}</span>
          <p>{scen.a2}</p>
        </div>
      </div>
    </div>

    <div class="pair">
      {@render resp('Before: base model', scen.base?.[arm] ?? [], ex.b, false)}
      <div class="arrow" aria-hidden="true">→</div>
      {@render resp(`After: trained on the row value`, ex.ft, ex.f, ex.mock)}
    </div>
    {#if ex.fj}
      <div class="judge"><span class="eyebrow">Judge on the “after” response</span><p>{ex.fj}</p></div>
    {/if}
  </div>
{/if}

{#snippet resp(title, turns, score, mock)}
  <div class="resp">
    <div class="resp-head">
      <span class="resp-title">{title}</span>
      <span class="pill num" style="background:{scoreColor(score)}1a; color:{scoreColor(score)}">
        {name(v2)}: {score.toFixed(2)}
      </span>
    </div>
    {#if mock || !turns.length}
      <div class="placeholder">Transcript pending.</div>
    {:else}
      {#each turns as t}
        <div class="turn {t.r}"><span class="role">{t.r === 'assistant' ? modelLabel : 'User'}</span>{t.t}</div>
      {/each}
    {/if}
  </div>
{/snippet}

<style>
  .flip { display: flex; flex-direction: column; gap: 14px; }
  .prompt { white-space: pre-wrap; font-size: 13px; color: var(--ink); background: var(--surface-2); border-radius: 8px; padding: 10px 12px; margin-top: 6px; }
  .prompt.clamped { display: -webkit-box; -webkit-line-clamp: 5; line-clamp: 5; -webkit-box-orient: vertical; overflow: hidden; }
  .role { display: block; font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 2px; }
  .link { border: 0; background: none; color: var(--accent); cursor: pointer; padding: 4px 0; font-size: 12px; }
  .actions { display: grid; grid-template-columns: 1fr; gap: 6px; margin-top: 6px; }
  .act { border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; font-size: 12.5px; }
  .act p { margin: 4px 0 0; color: var(--ink-2); }
  .act.aligned { border-color: var(--div-pos); }
  .act .tag { font-size: 11px; font-weight: 600; color: var(--ink-2); }
  .act.aligned .tag::after { content: ' · supports evaluated value'; color: var(--div-pos); }
  .pair { display: grid; grid-template-columns: 1fr; gap: 6px; }
  .arrow { text-align: center; color: var(--muted); font-size: 18px; line-height: 1; transform: rotate(90deg); }
  .resp { border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; background: var(--surface); }
  .resp-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 6px; }
  .resp-title { font-size: 12px; font-weight: 600; }
  .turn { white-space: pre-wrap; font-size: 12.5px; color: var(--ink-2); margin-top: 6px; }
  .turn.user { color: var(--muted); }
  .placeholder { font-size: 12px; color: var(--muted); font-style: italic; }
  .judge p { margin: 4px 0 0; font-size: 12px; color: var(--ink-2); }
  .loading { padding: 20px 0; }
</style>
