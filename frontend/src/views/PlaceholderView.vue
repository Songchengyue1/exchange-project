<script setup lang="ts">
defineProps<{
  title: string
  subtitle: string
}>()
</script>

<template>
  <section class="wrap">
    <p class="eyebrow ds-label-caps">Coming soon</p>
    <h1 class="title">{{ title }}</h1>
    <p class="sub">{{ subtitle }}</p>
  </section>
</template>

<style scoped>
.wrap {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-xxl) var(--space-lg) var(--space-section);
}

.eyebrow {
  margin: 0 0 var(--space-md);
  color: var(--color-muted);
}

.title {
  margin: 0 0 var(--space-md);
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  color: var(--color-on-dark);
}

.sub {
  margin: 0;
  max-width: 52ch;
  font-size: 16px;
  font-weight: 300;
  line-height: 1.5;
  color: var(--color-body);
}
</style>
