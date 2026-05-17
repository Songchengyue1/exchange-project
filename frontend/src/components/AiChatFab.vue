<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useAiChat } from '../composables/useAiChat'
import {
  clampFabPosition,
  defaultFabPosition,
  FAB_SIZE,
  loadFabPosition,
  saveFabPosition,
} from '../composables/useAiFabPosition'

const { open, show } = useAiChat()

const ready = ref(false)
const posX = ref(0)
const posY = ref(0)
const dragging = ref(false)
const hovered = ref(false)

let dragOrigin = { pointerX: 0, pointerY: 0, x: 0, y: 0 }
let didDrag = false
const DRAG_THRESHOLD = 6

function applyPosition() {
  const loaded = loadFabPosition()
  const p = clampFabPosition(loaded ?? defaultFabPosition())
  posX.value = p.x
  posY.value = p.y
}

function onResize() {
  const p = clampFabPosition({ x: posX.value, y: posY.value })
  posX.value = p.x
  posY.value = p.y
  saveFabPosition(p)
}

function onPointerDown(e: PointerEvent) {
  if (e.button !== 0) return
  dragging.value = true
  didDrag = false
  dragOrigin = {
    pointerX: e.clientX,
    pointerY: e.clientY,
    x: posX.value,
    y: posY.value,
  }
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
}

function onPointerMove(e: PointerEvent) {
  if (!dragging.value) return
  const dx = e.clientX - dragOrigin.pointerX
  const dy = e.clientY - dragOrigin.pointerY
  if (Math.abs(dx) > DRAG_THRESHOLD || Math.abs(dy) > DRAG_THRESHOLD) {
    didDrag = true
  }
  const p = clampFabPosition({
    x: dragOrigin.x + dx,
    y: dragOrigin.y + dy,
  })
  posX.value = p.x
  posY.value = p.y
}

function onPointerUp(e: PointerEvent) {
  if (!dragging.value) return
  dragging.value = false
  ;(e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId)
  saveFabPosition({ x: posX.value, y: posY.value })
  if (!didDrag) {
    show()
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    show()
  }
}

onMounted(() => {
  applyPosition()
  ready.value = true
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})
</script>

<template>
  <Teleport to="body">
    <button
      v-show="ready && !open"
      type="button"
      class="ai-fab"
      :class="{ 'ai-fab--dragging': dragging, 'ai-fab--hover': hovered && !dragging }"
      :style="{ left: `${posX}px`, top: `${posY}px`, width: `${FAB_SIZE}px`, height: `${FAB_SIZE}px` }"
      aria-label="打开 AI 助手"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
      @mouseenter="hovered = true"
      @mouseleave="hovered = false"
      @keydown="onKeydown"
    >
      <span class="ai-fab__stripe" aria-hidden="true" />
      <span class="ai-fab__icon" aria-hidden="true">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M12 3C7.03 3 3 6.58 3 11c0 2.02.9 3.86 2.38 5.24L4 21l4.9-1.28A8.4 8.4 0 0 0 12 19c4.97 0 9-3.58 9-8s-4.03-8-9-8Z"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linejoin="round"
          />
          <circle cx="9" cy="11" r="1" fill="currentColor" />
          <circle cx="12" cy="11" r="1" fill="currentColor" />
          <circle cx="15" cy="11" r="1" fill="currentColor" />
        </svg>
      </span>
      <span class="ai-fab__label">AI</span>
    </button>
  </Teleport>
</template>

<style scoped>
.ai-fab {
  position: fixed;
  z-index: 960;
  margin: 0;
  padding: 0;
  border: 1px solid var(--color-hairline);
  border-radius: 50%;
  background: linear-gradient(165deg, var(--color-surface-elevated) 0%, var(--color-surface-card) 100%);
  color: var(--color-on-dark);
  cursor: grab;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  overflow: hidden;
  box-shadow:
    0 8px 28px rgba(0, 0, 0, 0.45),
    0 0 0 1px rgba(255, 255, 255, 0.04) inset;
  touch-action: none;
  user-select: none;
  transition:
    box-shadow var(--duration-normal) var(--ease-out),
    transform var(--duration-fast) var(--ease-out),
    border-color var(--duration-fast) ease;
}

.ai-fab--hover {
  transform: translateY(-4px) scale(1.04);
  border-color: var(--color-body-strong);
  box-shadow:
    0 14px 40px rgba(0, 0, 0, 0.55),
    0 0 24px rgba(0, 102, 177, 0.15);
}

.ai-fab--dragging {
  cursor: grabbing;
  transform: scale(1.06);
  border-color: var(--color-on-dark);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.6);
  transition: none;
}

.ai-fab:focus-visible {
  outline: 2px solid var(--color-m-blue-light);
  outline-offset: 3px;
}

.ai-fab__stripe {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(
    90deg,
    var(--color-m-blue-light),
    var(--color-m-blue-dark),
    var(--color-m-red)
  );
  opacity: 0.9;
}

.ai-fab__icon {
  display: flex;
  margin-top: 4px;
  line-height: 0;
  opacity: 0.95;
}

.ai-fab__label {
  font-family: var(--font-display);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  line-height: 1;
  color: var(--color-body-strong);
}

.ai-fab--hover .ai-fab__label {
  color: var(--color-on-dark);
}

@media (prefers-reduced-motion: reduce) {
  .ai-fab,
  .ai-fab--hover {
    transition: none;
    transform: none;
  }

  .ai-fab--dragging {
    transform: none;
  }
}
</style>
