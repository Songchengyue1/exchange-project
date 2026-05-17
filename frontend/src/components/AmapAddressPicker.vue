<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  AMAP_SETUP_HINT,
  getAmapKey,
  getAmapSecurityCode,
  loadAmapScript,
  runAmapPlugins,
  type AmapPoi,
} from '../lib/amap'
import type { UserAddressInput } from '../types/address'

const props = defineProps<{
  modelValue: UserAddressInput
}>()

const emit = defineEmits<{
  'update:modelValue': [UserAddressInput]
}>()

const amapKey = getAmapKey()
const mapEl = ref<HTMLElement | null>(null)
const searchInputId = `amap-search-${Math.random().toString(36).slice(2)}`
const mapReady = ref(false)
const mapError = ref('')
const searching = ref(false)
const suggestions = ref<AmapPoi[]>([])

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let map: any = null
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let marker: any = null

function patch(partial: Partial<UserAddressInput>) {
  emit('update:modelValue', { ...props.modelValue, ...partial })
}

function setFromPoi(poi: AmapPoi) {
  patch({
    poi_name: poi.name,
    province: poi.pname ?? props.modelValue.province,
    city: poi.cityname ?? props.modelValue.city,
    district: poi.adname ?? props.modelValue.district,
    detail: poi.address || poi.name,
    latitude: poi.location.lat,
    longitude: poi.location.lng,
  })
  moveMarker(poi.location.lng, poi.location.lat)
}

function moveMarker(lng: number, lat: number) {
  if (!map || !marker) return
  const pos: [number, number] = [lng, lat]
  marker.setPosition(pos)
  map.setCenter(pos)
  map.setZoom(16)
}

async function searchPlaces(keyword: string) {
  if (!keyword.trim() || !window.AMap) {
    suggestions.value = []
    return
  }
  searching.value = true
  try {
    const list = await runAmapPlugins(['AMap.PlaceSearch'], () => {
      return new Promise<AmapPoi[]>((resolve) => {
        const PlaceSearch = (window as unknown as { AMap: { PlaceSearch: new (o: object) => PlaceSearchInst } })
          .AMap.PlaceSearch
        const ps = new PlaceSearch({ pageSize: 8, citylimit: false })
        ps.search(keyword, (status: string, result: { poiList?: { pois?: AmapPoi[] } }) => {
          if (status === 'complete' && result.poiList?.pois) {
            resolve(result.poiList.pois)
          } else {
            resolve([])
          }
        })
      })
    })
    suggestions.value = list
  } catch {
    suggestions.value = []
  } finally {
    searching.value = false
  }
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
const searchKeyword = ref('')

watch(searchKeyword, (kw) => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    void searchPlaces(kw)
  }, 320)
})

async function initMap() {
  if (!mapEl.value || !window.AMap) return
  const lng = props.modelValue.longitude ?? 115.858
  const lat = props.modelValue.latitude ?? 28.683
  map = new window.AMap.Map(mapEl.value, {
    zoom: 14,
    center: [lng, lat],
    viewMode: '2D',
  })
  marker = new window.AMap.Marker({ position: [lng, lat], map })
  map.on('click', (e: { lnglat: { lng: number; lat: number } }) => {
    const { lng: glng, lat: glat } = e.lnglat
    patch({ latitude: glat, longitude: glng })
    marker?.setPosition([glng, glat])
    void reverseGeocode(glng, glat)
  })
  mapReady.value = true
}

type PlaceSearchInst = {
  search: (keyword: string, cb: (status: string, result: { poiList?: { pois?: AmapPoi[] } }) => void) => void
}

async function reverseGeocode(lng: number, lat: number) {
  if (!window.AMap) return
  try {
    await runAmapPlugins(['AMap.Geocoder'], () => {
      const Geocoder = (window as unknown as { AMap: { Geocoder: new () => GeocoderInst } }).AMap.Geocoder
      const geo = new Geocoder()
      geo.getAddress([lng, lat], (status: string, result: GeocoderResult) => {
        if (status !== 'complete' || !result.regeocode) return
        const c = result.regeocode.addressComponent
        patch({
          province: c.province || props.modelValue.province,
          city: (Array.isArray(c.city) ? c.city[0] : c.city) || props.modelValue.city,
          district: c.district || props.modelValue.district,
          detail: result.regeocode.formattedAddress || props.modelValue.detail,
        })
      })
    })
  } catch {
    /* ignore */
  }
}

type GeocoderInst = {
  getAddress: (lnglat: [number, number], cb: (status: string, result: GeocoderResult) => void) => void
}

type GeocoderResult = {
  regeocode?: {
    formattedAddress?: string
    addressComponent: {
      province?: string
      city?: string | string[]
      district?: string
    }
  }
}

onMounted(async () => {
  if (!amapKey) {
    mapError.value = '未配置 VITE_AMAP_KEY，可在 .env 中填写高德 Web 端 Key 后使用地图选点；仍可手动填写下方地址。'
    return
  }
  mapError.value = ''
  try {
    await loadAmapScript(amapKey)
    await nextTick()
    await initMap()
  } catch (e) {
    const detail = e instanceof Error ? e.message : '地图初始化失败'
    const needSecurity = !getAmapSecurityCode()
    mapError.value = [
      '地图无法使用（常见为 Key 类型错误或缺少安全密钥，控制台会出现 USERKEY_PLAT_NOMATCH）。',
      AMAP_SETUP_HINT,
      needSecurity ? '当前未配置 VITE_AMAP_SECURITY_CODE。' : '',
      `详情：${detail}`,
    ]
      .filter(Boolean)
      .join(' ')
  }
})

onUnmounted(() => {
  map?.destroy()
  map = null
  marker = null
})
</script>

<template>
  <div class="picker">
    <p v-if="mapError" class="picker__warn">{{ mapError }}</p>

    <div class="picker__row">
      <div class="ds-field picker__field">
        <label class="ds-label" :for="searchInputId">搜索地点（高德）</label>
        <input
          :id="searchInputId"
          v-model="searchKeyword"
          class="ds-input"
          type="search"
          placeholder="小区、大厦、道路门牌号…"
          autocomplete="off"
        />
        <p v-if="searching" class="picker__hint">搜索中…</p>
        <ul v-if="suggestions.length" class="suggest">
          <li v-for="(poi, i) in suggestions" :key="i">
            <button type="button" class="suggest__btn" @click="setFromPoi(poi)">
              <strong>{{ poi.name }}</strong>
              <span>{{ poi.address }}</span>
            </button>
          </li>
        </ul>
      </div>
    </div>

    <div ref="mapEl" class="picker__map" :class="{ 'picker__map--off': !mapReady }">
      <p v-if="!mapReady && !mapError" class="picker__map-ph">地图加载中…</p>
    </div>

    <div class="picker__grid">
      <div class="ds-field">
        <label class="ds-label">标签</label>
        <input
          :value="modelValue.label"
          class="ds-input"
          placeholder="家 / 公司"
          @input="patch({ label: ($event.target as HTMLInputElement).value })"
        />
      </div>
      <div class="ds-field">
        <label class="ds-label">联系人</label>
        <input
          :value="modelValue.contact_name"
          class="ds-input"
          @input="patch({ contact_name: ($event.target as HTMLInputElement).value })"
        />
      </div>
      <div class="ds-field">
        <label class="ds-label">手机号</label>
        <input
          :value="modelValue.phone"
          class="ds-input"
          @input="patch({ phone: ($event.target as HTMLInputElement).value })"
        />
      </div>
      <div class="ds-field picker__field--wide">
        <label class="ds-label">详细地址</label>
        <input
          :value="modelValue.detail"
          class="ds-input"
          @input="patch({ detail: ($event.target as HTMLInputElement).value })"
        />
      </div>
    </div>
    <label class="picker__default">
      <input
        type="checkbox"
        :checked="!!modelValue.is_default"
        @change="patch({ is_default: ($event.target as HTMLInputElement).checked })"
      />
      设为默认地址
    </label>
  </div>
</template>

<style scoped>
.picker__warn {
  margin: 0 0 var(--space-md);
  padding: var(--space-sm) var(--space-md);
  font-size: 13px;
  color: var(--color-body);
  background: rgba(226, 39, 24, 0.08);
  border: 1px solid rgba(226, 39, 24, 0.25);
}

.picker__map {
  height: 220px;
  margin-bottom: var(--space-md);
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-soft);
  position: relative;
}

.picker__map--off {
  display: flex;
  align-items: center;
  justify-content: center;
}

.picker__map-ph {
  margin: 0;
  font-size: 13px;
  color: var(--color-muted);
}

.picker__grid {
  display: grid;
  gap: var(--space-sm);
  grid-template-columns: 1fr 1fr;
}

.picker__field--wide {
  grid-column: 1 / -1;
}

.suggest {
  list-style: none;
  margin: var(--space-xs) 0 0;
  padding: 0;
  border: 1px solid var(--color-hairline);
  max-height: 200px;
  overflow-y: auto;
}

.suggest__btn {
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  border: none;
  border-bottom: 1px solid var(--color-hairline);
  background: var(--color-surface-card);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.suggest__btn:hover {
  background: var(--color-surface-elevated);
}

.suggest__btn strong {
  font-size: 14px;
  color: var(--color-on-dark);
}

.suggest__btn span {
  font-size: 12px;
  color: var(--color-muted);
}

.picker__hint {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--color-muted);
}

.picker__default {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: var(--space-md);
  font-size: 14px;
  color: var(--color-body);
  cursor: pointer;
}
</style>
