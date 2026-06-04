<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, type RouteLocationRaw } from 'vue-router'

export type HeroSlide = {
  id: string | number
  title: string
  subtitle?: string
  image?: string | null
  tag?: string
  to: RouteLocationRaw
}

const props = withDefaults(
  defineProps<{
    slides: HeroSlide[]
    intervalMs?: number
  }>(),
  { intervalMs: 3500 },
)

const index = ref(0)
const paused = ref(false)
let timer: ReturnType<typeof setInterval> | null = null

const count = computed(() => props.slides.length)
function goTo(i: number) {
  if (!count.value) return
  index.value = ((i % count.value) + count.value) % count.value
}

function next() {
  goTo(index.value + 1)
}

function prev() {
  goTo(index.value - 1)
}

function startTimer() {
  stopTimer()
  if (count.value <= 1) return
  timer = setInterval(() => {
    if (!paused.value) next()
  }, props.intervalMs)
}

function stopTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

watch(
  () => props.slides.length,
  () => {
    if (index.value >= count.value) index.value = 0
    startTimer()
  },
)

onMounted(startTimer)
onUnmounted(stopTimer)
</script>

<template>
  <div
    v-if="count"
    class="carousel"
    @mouseenter="paused = true"
    @mouseleave="paused = false"
  >
    <div class="carousel__viewport">
      <RouterLink
        v-for="(slide, i) in slides"
        :key="slide.id"
        class="carousel__slide"
        :class="{ 'carousel__slide--on': i === index }"
        :to="slide.to"
        :aria-hidden="i !== index"
        :tabindex="i === index ? 0 : -1"
      >
        <img v-if="slide.image" class="carousel__img" :src="slide.image" :alt="slide.title" />
        <div v-else class="carousel__ph" aria-hidden="true" />
        <div class="carousel__shade" />
        <div class="carousel__copy">
          <span v-if="slide.tag" class="carousel__tag ds-label-caps">{{ slide.tag }}</span>
          <p class="carousel__title">{{ slide.title }}</p>
          <p v-if="slide.subtitle" class="carousel__sub">{{ slide.subtitle }}</p>
        </div>
      </RouterLink>
    </div>

    <div class="carousel__stripe" aria-hidden="true" />

    <button
      v-if="count > 1"
      type="button"
      class="carousel__nav carousel__nav--prev"
      aria-label="上一张"
      @click.prevent="prev"
    >
      <svg class="carousel__nav-icon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M14.5 5L8 12l6.5 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </button>
    <button
      v-if="count > 1"
      type="button"
      class="carousel__nav carousel__nav--next"
      aria-label="下一张"
      @click.prevent="next"
    >
      <svg class="carousel__nav-icon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M9.5 5L16 12l-6.5 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </button>

    <div v-if="count > 1" class="carousel__dots" role="tablist" aria-label="轮播切换">
      <button
        v-for="(slide, i) in slides"
        :key="'dot-' + slide.id"
        type="button"
        class="carousel__dot"
        :class="{ 'carousel__dot--on': i === index }"
        role="tab"
        :aria-selected="i === index"
        :aria-label="`第 ${i + 1} 张：${slide.title}`"
        @click="goTo(i)"
      />
    </div>
  </div>
  <div v-else class="carousel carousel--empty">
    <p class="carousel__empty-text">暂无推荐展示</p>
  </div>
</template>

<style scoped>
.carousel {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 10;
  min-height: 320px;
  max-height: min(56vh, 520px);
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-card);
  overflow: hidden;
}

.carousel--empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.carousel__empty-text {
  margin: 0;
  font-size: 14px;
  color: var(--color-muted);
}

.carousel__viewport {
  position: absolute;
  inset: 0;
}

.carousel__slide {
  position: absolute;
  inset: 0;
  display: block;
  text-decoration: none;
  color: inherit;
  opacity: 0;
  transition: opacity 0.55s var(--ease-out);
  pointer-events: none;
}

.carousel__slide--on {
  opacity: 1;
  pointer-events: auto;
  z-index: 1;
}

.carousel__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.carousel__ph {
  width: 100%;
  height: 100%;
  background: linear-gradient(
    135deg,
    var(--color-surface-soft) 0%,
    var(--color-carbon-gray) 45%,
    var(--color-surface-elevated) 100%
  );
}

.carousel__shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to top,
    rgba(0, 0, 0, 0.82) 0%,
    rgba(0, 0, 0, 0.25) 45%,
    rgba(0, 0, 0, 0.08) 100%
  );
  pointer-events: none;
}

.carousel__copy {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: var(--space-lg);
  z-index: 2;
}

.carousel__tag {
  display: inline-block;
  margin-bottom: var(--space-xs);
  padding: 2px 8px;
  font-size: 10px;
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(0, 0, 0, 0.35);
}

.carousel__title {
  margin: 0 0 4px;
  font-size: clamp(20px, 2.5vw, 26px);
  font-weight: 700;
  line-height: 1.2;
  color: #ffffff;
}

.carousel__sub {
  margin: 0;
  font-size: 13px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.4;
}

.carousel__stripe {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 3px;
  z-index: 3;
  background: linear-gradient(
    90deg,
    var(--color-m-blue-light) 0%,
    var(--color-m-blue-dark) 50%,
    var(--color-m-red) 100%
  );
  pointer-events: none;
}

.carousel__nav {
  position: absolute;
  top: 50%;
  z-index: 4;
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.55);
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(10px);
  color: #ffffff;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  opacity: 0;
  display: grid;
  place-items: center;
  box-shadow:
    0 12px 32px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(0, 0, 0, 0.08) inset;
  transition:
    opacity var(--duration-fast) ease,
    transform var(--duration-fast) var(--ease-out),
    background-color var(--duration-fast) ease,
    border-color var(--duration-fast) ease,
    box-shadow var(--duration-normal) var(--ease-out);
}

.carousel__nav-icon {
  width: 20px;
  height: 20px;
  display: block;
}

.carousel:hover .carousel__nav {
  opacity: 1;
}

.carousel__nav:hover {
  transform: translateY(-50%) scale(1.06);
  background: rgba(0, 0, 0, 0.55);
  border-color: rgba(255, 255, 255, 0.8);
  box-shadow:
    0 16px 44px rgba(0, 0, 0, 0.28),
    0 0 0 1px rgba(255, 255, 255, 0.08) inset;
}

.carousel__nav:active {
  transform: translateY(-50%) scale(0.98);
}

.carousel__nav:focus-visible {
  outline: 2px solid rgba(255, 255, 255, 0.9);
  outline-offset: 2px;
}

.carousel__nav--prev {
  left: var(--space-sm);
}

.carousel__nav--next {
  right: var(--space-sm);
}

.carousel__dots {
  position: absolute;
  right: var(--space-md);
  bottom: calc(var(--space-lg) + 52px);
  z-index: 4;
  display: flex;
  gap: 6px;
}

.carousel__dot {
  width: 8px;
  height: 8px;
  padding: 0;
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: transparent;
  cursor: pointer;
  transition:
    background-color var(--duration-fast) ease,
    transform var(--duration-fast) ease;
}

.carousel__dot--on {
  background: #ffffff;
  transform: scale(1.15);
}

@media (max-width: 900px) {
  .carousel {
    min-height: 240px;
    max-height: min(48vh, 400px);
    aspect-ratio: 16 / 10;
  }

  .carousel__nav {
    opacity: 1;
  }
}
</style>
