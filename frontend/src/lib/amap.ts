const AMAP_SCRIPT_ID = 'amap-js-sdk'

export type AmapPoi = {
  name: string
  address: string
  location: { lng: number; lat: number }
  pname?: string
  cityname?: string
  adname?: string
}

declare global {
  interface Window {
    _AMapSecurityConfig?: { securityJsCode: string }
    AMap?: {
      Map: new (el: HTMLElement | string, opts: Record<string, unknown>) => AmapMap
      Marker: new (opts: Record<string, unknown>) => AmapMarker
      plugin: (names: string[], cb: () => void) => void
      convertFrom: (
        lnglat: [number, number],
        type: string,
        cb: (status: string, result: { locations?: { lng: number; lat: number }[] }) => void,
      ) => void
    }
  }
}

type AmapMap = {
  setCenter: (pos: [number, number]) => void
  setZoom: (z: number) => void
  on: (event: string, cb: (e: { lnglat: { lng: number; lat: number } }) => void) => void
  destroy: () => void
}

type AmapMarker = {
  setPosition: (pos: [number, number]) => void
}

export function getAmapKey(): string {
  return (import.meta.env.VITE_AMAP_KEY as string | undefined)?.trim() ?? ''
}

/** JS API 2.0 需与 Key 同应用下的「安全密钥」 */
export function getAmapSecurityCode(): string {
  return (import.meta.env.VITE_AMAP_SECURITY_CODE as string | undefined)?.trim() ?? ''
}

export function applyAmapSecurityConfig(): void {
  const code = getAmapSecurityCode()
  if (code) {
    window._AMapSecurityConfig = { securityJsCode: code }
  }
}

export const AMAP_SETUP_HINT =
  '请在 https://console.amap.com 创建「Web端(JS API)」应用（不要用「Web服务」Key）。' +
  '复制 Key 与安全密钥到 frontend/.env：VITE_AMAP_KEY、VITE_AMAP_SECURITY_CODE；' +
  '白名单添加 localhost、127.0.0.1。'

export function loadAmapScript(key: string): Promise<void> {
  if (!key) return Promise.reject(new Error('未配置高德地图 Key'))
  applyAmapSecurityConfig()
  if (!getAmapSecurityCode()) {
    console.warn('[amap] 未配置 VITE_AMAP_SECURITY_CODE，JS API 2.0 可能无法正常使用')
  }
  if (window.AMap) return Promise.resolve()

  const existing = document.getElementById(AMAP_SCRIPT_ID)
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('高德地图加载失败')))
    })
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.id = AMAP_SCRIPT_ID
    script.async = true
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(key)}&plugin=AMap.AutoComplete,AMap.PlaceSearch,AMap.Geocoder`
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('高德地图加载失败'))
    document.head.appendChild(script)
  })
}

export function runAmapPlugins<T>(names: string[], run: () => T): Promise<T> {
  return new Promise((resolve, reject) => {
    if (!window.AMap) {
      reject(new Error('高德地图未就绪'))
      return
    }
    window.AMap.plugin(names, () => {
      try {
        resolve(run())
      } catch (e) {
        reject(e)
      }
    })
  })
}
