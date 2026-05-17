const STORAGE_KEY = 'ai_fab_position_v1'

export type FabPosition = { x: number; y: number }

export const FAB_SIZE = 56
export const FAB_MARGIN = 20

export function defaultFabPosition(): FabPosition {
  if (typeof window === 'undefined') {
    return { x: 320, y: 520 }
  }
  return {
    x: Math.max(FAB_MARGIN, window.innerWidth - FAB_SIZE - FAB_MARGIN),
    y: Math.max(FAB_MARGIN, window.innerHeight - FAB_SIZE - FAB_MARGIN),
  }
}

export function loadFabPosition(): FabPosition | null {
  if (typeof localStorage === 'undefined') return null
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const p = JSON.parse(raw) as FabPosition
    if (Number.isFinite(p.x) && Number.isFinite(p.y)) return p
  } catch {
    /* ignore */
  }
  return null
}

export function saveFabPosition(pos: FabPosition) {
  if (typeof localStorage === 'undefined') return
  localStorage.setItem(STORAGE_KEY, JSON.stringify(pos))
}

export function clampFabPosition(pos: FabPosition): FabPosition {
  if (typeof window === 'undefined') return pos
  const maxX = window.innerWidth - FAB_SIZE - FAB_MARGIN
  const maxY = window.innerHeight - FAB_SIZE - FAB_MARGIN
  return {
    x: Math.min(Math.max(FAB_MARGIN, pos.x), Math.max(FAB_MARGIN, maxX)),
    y: Math.min(Math.max(FAB_MARGIN, pos.y), Math.max(FAB_MARGIN, maxY)),
  }
}
