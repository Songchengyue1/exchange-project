<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  createAddress,
  deleteAddress,
  listAddresses,
  setDefaultAddress,
  updateAddress,
} from '../api/addresses'
import { showConfirm } from '../composables/useConfirm'
import { useAuthStore } from '../stores/auth'
import type { UserAddress, UserAddressInput } from '../types/address'
import AmapAddressPicker from './AmapAddressPicker.vue'

const props = defineProps<{
  modelValue: number | null
  requireAddress?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [number | null]
}>()

const auth = useAuthStore()
const addresses = ref<UserAddress[]>([])
const loading = ref(true)
const error = ref('')
const dialogOpen = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)

const emptyForm = (): UserAddressInput => ({
  label: '家',
  contact_name: auth.user?.nickname ?? '',
  phone: auth.user?.phone ?? '',
  province: null,
  city: null,
  district: null,
  detail: '',
  poi_name: null,
  latitude: null,
  longitude: null,
  is_default: addresses.value.length === 0,
})

const form = ref<UserAddressInput>(emptyForm())

const selected = computed(() => addresses.value.find((a) => a.id === props.modelValue) ?? null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    addresses.value = await listAddresses()
    if (!props.modelValue) {
      const def = addresses.value.find((a) => a.is_default) ?? addresses.value[0]
      if (def) emit('update:modelValue', def.id)
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载地址失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

watch(
  () => props.modelValue,
  (id) => {
    if (id) localStorage.setItem('checkout_address_id', String(id))
  },
)

function select(id: number) {
  emit('update:modelValue', id)
}

function openCreate() {
  editingId.value = null
  form.value = emptyForm()
  dialogOpen.value = true
}

function openEdit(addr: UserAddress) {
  editingId.value = addr.id
  form.value = {
    label: addr.label,
    contact_name: addr.contact_name,
    phone: addr.phone,
    province: addr.province,
    city: addr.city,
    district: addr.district,
    detail: addr.detail,
    poi_name: addr.poi_name,
    latitude: addr.latitude,
    longitude: addr.longitude,
    is_default: addr.is_default,
  }
  dialogOpen.value = true
}

function closeDialog() {
  dialogOpen.value = false
}

async function saveAddress() {
  if (!form.value.contact_name.trim() || !form.value.phone.trim() || !form.value.detail.trim()) {
    error.value = '请填写联系人、手机号与详细地址'
    return
  }
  saving.value = true
  error.value = ''
  try {
    let saved: UserAddress
    if (editingId.value != null) {
      saved = await updateAddress(editingId.value, form.value)
    } else {
      saved = await createAddress(form.value)
    }
    await load()
    emit('update:modelValue', saved.id)
    dialogOpen.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

async function remove(addr: UserAddress) {
  const ok = await showConfirm({
    title: '删除地址',
    message: `确定删除「${addr.label}」？`,
    confirmText: '删除',
    variant: 'danger',
  })
  if (!ok) return
  try {
    await deleteAddress(addr.id)
    if (props.modelValue === addr.id) emit('update:modelValue', null)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '删除失败'
  }
}

async function makeDefault(addr: UserAddress) {
  try {
    await setDefaultAddress(addr.id)
    await load()
    emit('update:modelValue', addr.id)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  }
}

defineExpose({
  validate: () => {
    if (!props.requireAddress) return true
    if (props.modelValue && selected.value) return true
    error.value = '请选择收货地址'
    return false
  },
})
</script>

<template>
  <div class="addr">
    <div class="addr__head">
      <h2 class="addr__title ds-label-caps">收货地址</h2>
      <button type="button" class="addr__add" @click="openCreate">+ 新增地址</button>
    </div>

    <p v-if="error" class="ds-form-error">{{ error }}</p>
    <p v-if="loading" class="muted">加载地址中…</p>

    <p v-else-if="!addresses.length" class="muted">
      暂无收货地址，请点击「新增地址」并在地图上选点。
    </p>

    <ul v-else class="addr__list">
      <li v-for="a in addresses" :key="a.id">
        <label class="addr__card" :class="{ 'addr__card--on': modelValue === a.id }">
          <input
            type="radio"
            name="checkout-address"
            class="addr__radio"
            :checked="modelValue === a.id"
            @change="select(a.id)"
          />
          <div class="addr__card-body">
            <div class="addr__card-top">
              <span class="addr__tag">{{ a.label }}</span>
              <span v-if="a.is_default" class="addr__default-pill">默认</span>
              <span class="addr__contact">{{ a.contact_name }} {{ a.phone }}</span>
            </div>
            <p class="addr__line">{{ a.formatted }}</p>
            <div class="addr__actions">
              <button type="button" class="link-btn" @click.prevent="openEdit(a)">编辑</button>
              <button v-if="!a.is_default" type="button" class="link-btn" @click.prevent="makeDefault(a)">
                设为默认
              </button>
              <button type="button" class="link-btn danger" @click.prevent="remove(a)">删除</button>
            </div>
          </div>
        </label>
      </li>
    </ul>

    <Teleport to="body">
      <div v-if="dialogOpen" class="dialog-backdrop" @click.self="closeDialog">
        <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="addr-dialog-title">
          <header class="dialog__head">
            <h3 id="addr-dialog-title">{{ editingId != null ? '编辑地址' : '新增地址' }}</h3>
            <button type="button" class="dialog__close" aria-label="关闭" @click="closeDialog">×</button>
          </header>
          <div class="dialog__body">
            <AmapAddressPicker v-model="form" />
          </div>
          <footer class="dialog__foot">
            <button type="button" class="ds-btn ds-btn--ghost" @click="closeDialog">取消</button>
            <button type="button" class="ds-btn" :disabled="saving" @click="saveAddress">
              {{ saving ? '保存中…' : '保存' }}
            </button>
          </footer>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.addr__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.addr__title {
  margin: 0;
  font-size: 12px;
  color: var(--color-muted);
}

.addr__add {
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-soft);
  color: var(--color-on-dark);
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
  border-radius: 8px;
}

.addr__add:hover {
  border-color: var(--color-on-dark);
}

.muted {
  font-size: 14px;
  color: var(--color-muted);
}

.addr__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.addr__card {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-soft);
  cursor: pointer;
  transition:
    border-color var(--duration-fast) ease,
    background-color var(--duration-fast) ease;
}

.addr__card--on {
  border-color: var(--color-on-dark);
  background: var(--color-surface-card);
  box-shadow: 0 0 0 1px var(--color-on-dark);
}

.addr__radio {
  margin-top: 4px;
  flex-shrink: 0;
  accent-color: var(--color-on-dark);
}

.addr__card-body {
  flex: 1;
  min-width: 0;
}

.addr__card-top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.addr__tag {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-dark);
  padding: 2px 8px;
  border: 1px solid var(--color-hairline);
}

.addr__default-pill {
  font-size: 11px;
  color: var(--color-body-strong);
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-elevated);
  padding: 1px 6px;
  border-radius: 999px;
}

.addr__contact {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-on-dark);
}

.addr__line {
  margin: 0 0 var(--space-sm);
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-body);
}

.addr__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.link-btn {
  background: none;
  border: none;
  padding: 0;
  font-size: 13px;
  color: var(--color-body-strong);
  cursor: pointer;
}

.link-btn:hover {
  text-decoration: underline;
}

.link-btn.danger {
  color: var(--color-m-red);
}

.dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg);
}

.dialog {
  width: min(100%, 560px);
  max-height: min(92vh, 720px);
  display: flex;
  flex-direction: column;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
}

.dialog__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--color-hairline);
}

.dialog__head h3 {
  margin: 0;
  font-size: 18px;
  color: var(--color-on-dark);
}

.dialog__close {
  border: none;
  background: none;
  font-size: 24px;
  line-height: 1;
  color: var(--color-muted);
  cursor: pointer;
}

.dialog__body {
  padding: var(--space-lg);
  overflow-y: auto;
}

.dialog__foot {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  border-top: 1px solid var(--color-hairline);
}
</style>
