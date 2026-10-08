<script>
  import Header from './lib/Header.svelte';
  import S1 from './sections/S1Generalization.svelte';
  import S2 from './sections/S2Predictors.svelte';
  import S3 from './sections/S3Taxonomy.svelte';
  import S4 from './sections/S4Builder.svelte';
  import { META } from './lib/meta.js';

  let showCite = $state(false);
  let copied = $state(false);
  function copyBib() {
    navigator.clipboard?.writeText(META.bibtex).then(() => {
      copied = true;
      setTimeout(() => (copied = false), 1500);
    });
  }

</script>

<Header />

<main id="top">
  <div class="hero prose">
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
      In this paper, we establish the task of <em>alignment generalization prediction</em>: predicting how
      fine-tuning a model to follow a given value changes its behavior across a wide range of heldout values. We use
      this to benchmark different methods of representing values. We then show that representations that do well on
      the generalization prediction task can also be applied to taxonomizing LLM values (ValueMap) and studying
      multi-value alignment targets.
    </p>
    <div class="cta ui">
      <a class="btn" href={META.arxivUrl}>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></svg>
        Paper
      </a>
      <a class="btn" href={META.codeUrl}>
        <svg viewBox="0 0 16 16" aria-hidden="true" class="fill"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z" /></svg>
        Code
      </a>
      <button class="btn" aria-expanded={showCite} onclick={() => (showCite = !showCite)}>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7h4v4c0 3-1.5 5-4 6M15 7h4v4c0 3-1.5 5-4 6" /></svg>
        Cite
      </button>
      <a class="btn primary" href="#generalization">Explore ↓</a>
    </div>
    {#if showCite}
      <div class="bib card">
        <button class="btn copy" onclick={copyBib}>{copied ? 'Copied' : 'Copy'}</button>
        <pre>{META.bibtex}</pre>
      </div>
    {/if}
  </div>

  <S1 />
  <S2 />
  <S3 />
  <S4 />

</main>

<style>
  .hero { padding-top: 72px; padding-bottom: 40px; text-align: center; }
  .hero > * { margin-left: auto; margin-right: auto; }
  h1 { max-width: 900px; font-size: 44px; line-height: 1.1; margin: 10px 0 18px; letter-spacing: -0.02em; }
  .authors { font-size: 16px; margin: 0 auto 4px; }
  .author { white-space: nowrap; }
  sup { font-size: 10px; margin-left: 1px; }
  .affs { font-size: 13px; display: flex; flex-wrap: wrap; justify-content: center; gap: 4px 14px; margin: 0 auto 28px; max-width: none; }
  .lede { font-size: 18px; line-height: 1.6; margin-bottom: 28px; }
  main { padding-bottom: 96px; }
  .cta { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
  .cta .btn { display: inline-flex; align-items: center; gap: 7px; text-decoration: none; padding: 9px 16px; font-size: 14px; }
  .cta svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
  .cta svg.fill { fill: currentColor; stroke: none; }
  .bib { position: relative; margin-top: 16px; padding: 14px 16px; text-align: left; }
  .bib pre { margin: 0; font-size: 12.5px; line-height: 1.5; white-space: pre-wrap; overflow-wrap: anywhere; padding-right: 56px; }
  .copy { position: absolute; top: 10px; right: 10px; padding: 3px 10px; font-size: 12px; }
  .cta .primary { background: var(--ink); color: #fff; border-color: var(--ink); }
  .cta .primary:hover { background: #333; }
  @media (max-width: 720px) { h1 { font-size: 32px; } }
</style>
