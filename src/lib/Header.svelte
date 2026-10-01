<script>
  import { onMount } from 'svelte';
  import { META, SECTIONS } from './meta.js';

  let active = $state(null);
  onMount(() => {
    const els = SECTIONS.map((s) => document.getElementById(s.id)).filter(Boolean);
    const onScroll = () => {
      const y = window.scrollY + window.innerHeight * 0.35;
      let cur = null;
      for (const el of els) if (el.offsetTop <= y) cur = el.id;
      active = cur;
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  });
</script>

<header class="ui">
  <div class="inner">
    <a class="brand" href="#top">{META.title}</a>
    <nav aria-label="Sections">
      {#each SECTIONS as s, n}
        <a href="#{s.id}" class:active={active === s.id} aria-current={active === s.id ? 'true' : undefined}>
          <span class="n num">{n + 1}</span>{s.label}
        </a>
      {/each}
    </nav>
    <div class="links">
      {#if META.paperUrl}<a href={META.paperUrl}>Paper</a>{/if}
      {#if META.codeUrl}<a href={META.codeUrl}>Code</a>{/if}
    </div>
  </div>
</header>

<style>
  header { position: sticky; top: 0; z-index: 40; height: var(--header-h); background: rgba(249, 249, 247, 0.9); backdrop-filter: saturate(1.4) blur(10px); border-bottom: 1px solid var(--grid); }
  .inner { max-width: var(--wide); margin: 0 auto; height: 100%; padding: 0 16px; display: flex; align-items: center; gap: 20px; }
  .brand { flex: 0 1 300px; font-weight: 700; font-size: 13.5px; line-height: 1.25; color: var(--ink); text-decoration: none; letter-spacing: -0.01em; }
  nav { display: flex; gap: 4px; flex: 1; justify-content: center; overflow-x: auto; scrollbar-width: none; }
  nav a { display: inline-flex; align-items: center; gap: 7px; padding: 6px 10px; border-radius: 999px; color: var(--ink-2); text-decoration: none; font-size: 14px; white-space: nowrap; transition: background .15s, color .15s; }
  nav a:hover { background: var(--surface-2); color: var(--ink); }
  nav a.active { background: var(--accent-soft); color: var(--ink); font-weight: 600; }
  .n { display: inline-grid; place-items: center; width: 18px; height: 18px; border-radius: 50%; font-size: 11px; background: var(--surface-2); color: var(--muted); }
  nav a.active .n { background: var(--accent); color: #fff; }
  .links { display: flex; gap: 14px; }
  .links a { font-size: 14px; color: var(--ink-2); text-decoration: none; }
  .links a:hover { color: var(--accent); }
  @media (max-width: 1240px) { .brand { display: none; } }
  @media (max-width: 720px) { .links { display: none; } nav { justify-content: flex-start; } nav a { padding: 6px 8px; } }
</style>
