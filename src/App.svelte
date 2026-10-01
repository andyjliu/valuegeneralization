<script>
  import Header from './lib/Header.svelte';
  import S1 from './sections/S1Generalization.svelte';
  import S2 from './sections/S2Predictors.svelte';
  import S3 from './sections/S3Taxonomy.svelte';
  import S4 from './sections/S4Builder.svelte';
  import { META } from './lib/meta.js';

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
      {#if META.paperUrl}<a class="btn primary" href={META.paperUrl}>Read the paper</a>{/if}
      {#if META.codeUrl}<a class="btn" href={META.codeUrl}>Code</a>{/if}
      <a class="btn" href="#generalization">Explore ↓</a>
    </div>
  </div>

  <S1 />
  <S2 />
  <S3 />
  <S4 />

</main>

<style>
  .hero { padding-top: 72px; padding-bottom: 40px; }
  h1 { max-width: 900px; font-size: 44px; line-height: 1.1; margin: 10px 0 18px; letter-spacing: -0.02em; }
  .authors { font-size: 16px; margin: 0 0 4px; }
  .author { white-space: nowrap; }
  sup { font-size: 10px; margin-left: 1px; }
  .affs { font-size: 13px; display: flex; flex-wrap: wrap; gap: 4px 14px; margin: 0 0 28px; }
  .lede { font-size: 18px; line-height: 1.6; margin-bottom: 28px; }
  main { padding-bottom: 96px; }
  .cta { display: flex; gap: 10px; flex-wrap: wrap; }
  .cta .btn { text-decoration: none; padding: 9px 16px; font-size: 14px; }
  .cta .primary { background: var(--ink); color: #fff; border-color: var(--ink); }
  .cta .primary:hover { background: #333; }
  @media (max-width: 720px) { h1 { font-size: 32px; } }
</style>
