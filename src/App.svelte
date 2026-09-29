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
      LLM developers post-train their models to exhibit prosocial values and behavioral traits, which are enumerated
      in an <a href="https://arxiv.org/abs/2404.10636">alignment target</a>. However, while recent post-training developments have yielded models that score highly on
      alignment evaluations, training models on sets of narrow behaviors still influences their behavior across
      unseen contexts and environments in unexpected ways. In this paper, we establish the task of <em>alignment
      generalization prediction</em>, i.e., predicting how fine-tuning a model to follow a given value changes its
      behavior across a wide range of heldout values. We conduct a large-scale analysis of alignment generalization
      effects across 66 values found in modern alignment targets, and benchmark representational techniques on the
      alignment generalization prediction task. We find that representations based on model activations when
      applying values in context significantly outperform methods based on textual descriptions of the values.
      Specifically, the best activations-based methods achieve correlations of ρ = 0.46 with our generalization
      matrix, compared with ρ = 0.06 from description-based baselines. We then show the applicability of
      representations that predict alignment generalization toward downstream tasks by using them to measure how
      similar the values in a multi-value alignment target are, which we find is significantly correlated with
      model robustness. Finally, we show initial evidence towards a shared, model-independent value space, which we
      use to develop the first taxonomy of LLM values grounded in empirical generalization dynamics. Our work
      demonstrates the importance of studying value generalization in LLMs and its application toward the more
      empirical design and training of model behavior.
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
