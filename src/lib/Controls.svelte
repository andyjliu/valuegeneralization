<script>
  import { MODEL_LABEL, SIZE_LABEL, METHOD_LABEL } from './data.js';
  let { model = $bindable('qwen'), size = $bindable('s'), method = $bindable('dpo'), children } = $props();
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
  <span class="ctl-label">Model size</span>
  <div class="seg" role="group" aria-label="Model size">
    {#each Object.entries(SIZE_LABEL[model]) as [k, label]}
      <button aria-pressed={size === k} onclick={() => (size = k)}>{label}</button>
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
