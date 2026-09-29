<script>
  import Header from './lib/Header.svelte';
  import S1 from './sections/S1Generalization.svelte';
  import S2 from './sections/S2Predictors.svelte';
  import S3 from './sections/S3Taxonomy.svelte';
  import S4 from './sections/S4Builder.svelte';
  import { META } from './lib/meta.js';

  let copied = $state(false);
  function copyBib() {
    navigator.clipboard?.writeText(META.bibtex).then(() => { copied = true; setTimeout(() => (copied = false), 1500); });
  }
</script>

<Header />

<main id="top">
  <div class="hero prose">
    <div class="eyebrow">Interactive paper companion</div>
    <h1>{META.title}</h1>
    <p class="authors ui">
      {#each META.authors as a, n}
        <span class="author">{a.name}<sup>{a.aff.join(',')}</sup></span>{n < META.authors.length - 1 ? ', ' : ''}
      {/each}
    </p>
    <p class="affs ui muted">
      {#each META.affiliations as aff, n}<span><sup>{n + 1}</sup>{aff}</span>{/each}
    </p>
    <p class="lede">
      Training a model to follow one value changes how it behaves on values it was never trained on. We measure
      this <em>alignment generalization</em> across 66 values, show that representations built from model
      activations can predict it before any training happens, and use those representations to judge how coherent
      an alignment target is and to map the space of LLM values.
    </p>
    <div class="stats ui">
      <div><span class="num big">0.46</span><span>Spearman ρ with generalization for activation-based representations, vs. 0.06 for description embeddings</span></div>
      <div><span class="num big">0.43</span><span>correlation between a target's persona-vector coherence and a trained model's prefill robustness</span></div>
      <div><span class="num big">266</span><span>values from real-world interactions mapped into four clusters by ValueMap</span></div>
    </div>
    <div class="cta ui">
      {#if META.paperUrl}<a class="btn primary" href={META.paperUrl}>Read the paper</a>{/if}
      {#if META.codeUrl}<a class="btn" href={META.codeUrl}>Code</a>{/if}
      <a class="btn" href="#generalization">Explore ↓</a>
    </div>
  </div>

  <S1 />
  <S2 />
  <S3 />
  <S4 />

  <footer class="prose ui">
    <h3>Citation</h3>
    <div class="bib card">
      <button class="btn copy" onclick={copyBib}>{copied ? 'Copied' : 'Copy'}</button>
      <pre>{META.bibtex}</pre>
    </div>
    <p class="muted small">
      Generalization matrices, predictor similarities, taxonomy and coherence values are exported directly from the
      paper's experiments. Scenario examples come from ConflictScope evaluations of each fine-tuned checkpoint.
    </p>
  </footer>
</main>

<style>
  .hero { padding-top: 72px; padding-bottom: 40px; }
  h1 { font-size: 44px; line-height: 1.1; margin: 10px 0 18px; letter-spacing: -0.02em; }
  .authors { font-size: 16px; margin: 0 0 4px; }
  .author { white-space: nowrap; }
  sup { font-size: 10px; margin-left: 1px; }
  .affs { font-size: 13px; display: flex; flex-wrap: wrap; gap: 4px 14px; margin: 0 0 28px; }
  .lede { font-size: 20px; line-height: 1.55; }
  .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 28px 0; }
  .stats div { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: var(--ink-2); border-top: 2px solid var(--ink); padding-top: 10px; }
  .big { font-size: 34px; font-weight: 700; color: var(--ink); letter-spacing: -0.02em; line-height: 1; }
  .cta { display: flex; gap: 10px; flex-wrap: wrap; }
  .cta .btn { text-decoration: none; padding: 9px 16px; font-size: 14px; }
  .cta .primary { background: var(--ink); color: #fff; border-color: var(--ink); }
  .cta .primary:hover { background: #333; }
  footer { padding: 80px 16px 80px; border-top: 1px solid var(--grid); margin-top: 60px; }
  footer h3 { font-size: 18px; }
  .bib { position: relative; padding: 14px 16px; }
  .bib pre { margin: 0; font-size: 12px; white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  .copy { position: absolute; top: 10px; right: 10px; }
  .small { font-size: 12.5px; margin-top: 16px; }
  @media (max-width: 720px) { h1 { font-size: 32px; } .stats { grid-template-columns: 1fr; } }
</style>
