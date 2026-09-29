<script>
  import { MODEL_LABEL, METHOD_LABEL } from './data.js';
  let { model = $bindable('qwen'), method = $bindable('dpo'), children } = $props();
</script>

<div class="ctl">
  <span class="ctl-label">Base model</span>
  <div class="seg" role="group" aria-label="Base model">
    {#each Object.entries(MODEL_LABEL) as [k, label]}
      <button aria-pressed={model === k} onclick={() => (model = k)}>{label}</button>
    {/each}
  </div>
</div>
<div class="ctl">
  <span class="ctl-label">Training method</span>
  <div class="seg" role="group" aria-label="Training method">
    {#each Object.entries(METHOD_LABEL) as [k, label]}
      <button aria-pressed={method === k} onclick={() => (method = k)}>{label}</button>
    {/each}
  </div>
</div>
{@render children?.()}
