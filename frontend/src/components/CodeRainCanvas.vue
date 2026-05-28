<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

const root = ref<HTMLElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)

const CHARSET =
  '酱菜二手交易平台login页面'

/** 每帧下落行数（约 0.45 ≈ 原先速度的 45%） */
const DROP_SPEED = 0.45

let raf = 0
let dropRows: number[] = []
let fontSize = 15
let columns = 0
let reducedMotion = false
let resizeObserver: ResizeObserver | null = null

function pickChar() {
  return CHARSET[Math.floor(Math.random() * CHARSET.length)] ?? '0'
}

function drawFrame(ctx: CanvasRenderingContext2D, w: number, h: number) {
  ctx.fillStyle = 'rgba(0, 0, 0, 0.05)'
  ctx.fillRect(0, 0, w, h)

  ctx.font = `700 ${fontSize}px "Inter", "SF Mono", "Menlo", monospace`
  ctx.textBaseline = 'top'

  for (let i = 0; i < columns; i++) {
    const x = i * fontSize
    const row = dropRows[i]!
    const headRow = Math.floor(row)
    const y = headRow * fontSize
    const head = pickChar()

    ctx.shadowColor = 'rgba(28, 105, 212, 0.9)'
    ctx.shadowBlur = 8
    ctx.fillStyle = '#e8f2ff'
    ctx.fillText(head, x, y)

    ctx.shadowBlur = 0
    if (headRow > 0) {
      ctx.fillStyle = 'rgba(28, 105, 212, 0.55)'
      ctx.fillText(pickChar(), x, y - fontSize)
      ctx.fillStyle = 'rgba(28, 105, 212, 0.28)'
      ctx.fillText(pickChar(), x, y - fontSize * 2)
    }

    dropRows[i] = row + DROP_SPEED
    if (dropRows[i]! * fontSize > h && Math.random() > 0.975) {
      dropRows[i] = 0
    }
  }
}

function drawStatic(ctx: CanvasRenderingContext2D, w: number, h: number) {
  ctx.fillStyle = '#000000'
  ctx.fillRect(0, 0, w, h)
  ctx.font = `500 ${fontSize}px "Inter", monospace`
  ctx.textBaseline = 'top'

  for (let y = 0; y < h; y += fontSize * 1.4) {
    for (let x = 0; x < w; x += fontSize * 0.85) {
      if (Math.random() > 0.92) {
        ctx.fillStyle = `rgba(28, 105, 212, ${0.12 + Math.random() * 0.2})`
        ctx.fillText(pickChar(), x, y)
      }
    }
  }
}

function loop() {
  const el = canvas.value
  const host = root.value
  if (!el || !host) return

  const ctx = el.getContext('2d')
  if (!ctx) return

  const w = host.clientWidth
  const h = host.clientHeight
  if (w < 1 || h < 1) {
    raf = requestAnimationFrame(loop)
    return
  }

  if (reducedMotion) {
    drawStatic(ctx, w, h)
    return
  }

  drawFrame(ctx, w, h)
  raf = requestAnimationFrame(loop)
}

function resize() {
  const el = canvas.value
  const host = root.value
  if (!el || !host) return

  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  const w = host.clientWidth
  const h = host.clientHeight

  el.width = Math.floor(w * dpr)
  el.height = Math.floor(h * dpr)
  el.style.width = `${w}px`
  el.style.height = `${h}px`

  const ctx = el.getContext('2d')
  if (!ctx) return
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.fillStyle = '#000000'
  ctx.fillRect(0, 0, w, h)

  fontSize = Math.max(12, Math.min(16, Math.round(w / 90)))
  columns = Math.max(1, Math.floor(w / fontSize))
  const prev = dropRows
  dropRows = Array.from(
    { length: columns },
    (_, i) => prev[i] ?? Math.random() * Math.max(1, h / fontSize),
  )
}

function start() {
  cancelAnimationFrame(raf)
  resize()
  if (reducedMotion) {
    const el = canvas.value
    const host = root.value
    const ctx = el?.getContext('2d')
    if (ctx && host) drawStatic(ctx, host.clientWidth, host.clientHeight)
    return
  }
  raf = requestAnimationFrame(loop)
}

function stop() {
  cancelAnimationFrame(raf)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  resizeObserver?.disconnect()
  resizeObserver = null
}

function onVisibilityChange() {
  if (document.hidden) {
    cancelAnimationFrame(raf)
    return
  }
  if (!reducedMotion) start()
}

onMounted(() => {
  reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  resize()
  start()
  document.addEventListener('visibilitychange', onVisibilityChange)

  if (root.value) {
    resizeObserver = new ResizeObserver(() => {
      resize()
      if (reducedMotion) {
        const el = canvas.value
        const host = root.value
        const ctx = el?.getContext('2d')
        if (ctx && host) drawStatic(ctx, host.clientWidth, host.clientHeight)
      }
    })
    resizeObserver.observe(root.value)
  }
})

onUnmounted(stop)
</script>

<template>
  <div ref="root" class="code-rain">
    <canvas ref="canvas" class="code-rain__canvas" aria-hidden="true" />
    <div class="code-rain__vignette" aria-hidden="true" />
  </div>
</template>

<style scoped>
.code-rain {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: var(--color-canvas);
}

.code-rain__canvas {
  display: block;
  width: 60%;
  height: 100%;
}

.code-rain__vignette {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 85% 70% at 50% 45%, transparent 0%, rgba(0, 0, 0, 0.55) 100%),
    linear-gradient(180deg, rgba(0, 0, 0, 0.35) 0%, transparent 28%, transparent 62%, rgba(0, 0, 0, 0.65) 100%);
}
</style>
