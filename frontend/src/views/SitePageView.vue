<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { SITE_PAGES, type SitePageKey } from '../content/sitePages'

const route = useRoute()

const page = computed(() => {
  const key = route.meta.sitePage as SitePageKey | undefined
  return key ? SITE_PAGES[key] : null
})
</script>

<template>
  <section v-if="page" class="wrap page-doc">
    <p class="eyebrow ds-label-caps">{{ page.eyebrow }}</p>
    <h1 class="title">{{ page.title }}</h1>
    <p v-if="page.lede" class="lede">{{ page.lede }}</p>
    <p class="updated">最后更新：{{ page.updatedAt }}</p>

    <article v-for="(section, i) in page.sections" :key="i" class="section">
      <h2 v-if="section.heading" class="section__title">{{ section.heading }}</h2>
      <p v-for="(para, j) in section.paragraphs ?? []" :key="`p-${j}`" class="section__p">{{ para }}</p>
      <ul v-if="section.list?.length" class="section__list">
        <li v-for="(item, k) in section.list" :key="`l-${k}`">{{ item }}</li>
      </ul>
    </article>

    <p class="back">
      <RouterLink to="/" class="text-link ds-label-caps">← 返回首页</RouterLink>
    </p>
  </section>
</template>

<style scoped>
.wrap {
  padding-top: var(--space-section);
  padding-bottom: var(--space-section);
}

.page-doc {
  max-width: 720px;
  margin: 0 auto;
  padding: var(--space-xxl) var(--space-lg);
}

.eyebrow {
  margin: 0 0 var(--space-md);
  color: var(--color-muted);
}

.title {
  margin: 0 0 var(--space-sm);
  font-size: clamp(26px, 3.5vw, 36px);
  font-weight: 700;
  color: var(--color-on-dark);
}

.lede {
  margin: 0 0 var(--space-md);
  font-size: 16px;
  font-weight: 400;
  line-height: 1.6;
  color: var(--color-body);
}

.updated {
  margin: 0 0 var(--space-xl);
  font-size: 12px;
  color: var(--color-muted);
}

.section {
  margin-bottom: var(--space-xl);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--color-hairline);
}

.section:last-of-type {
  border-bottom: none;
}

.section__title {
  margin: 0 0 var(--space-md);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-on-dark);
}

.section__p {
  margin: 0 0 var(--space-md);
  font-size: 15px;
  font-weight: 400;
  line-height: 1.65;
  color: var(--color-body);
}

.section__list {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 15px;
  font-weight: 400;
  line-height: 1.65;
  color: var(--color-body);
}

.section__list li + li {
  margin-top: var(--space-sm);
}

.back {
  margin: var(--space-xl) 0 0;
}

.text-link {
  color: var(--color-on-dark);
  text-decoration: none;
}

.text-link:hover {
  text-decoration: underline;
}
</style>
