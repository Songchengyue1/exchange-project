<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  createAdminCategory,
  deleteAdminCategory,
  listAdminCategories,
  updateAdminCategory,
} from '../api/admin'
import { showConfirm } from '../composables/useConfirm'
import type { CategoryPublic } from '../types/product'

const items = ref<CategoryPublic[]>([])
const loading = ref(true)
const error = ref('')
const busyId = ref<number | null>(null)

const newName = ref('')
const newSort = ref(0)
const editName = ref<Record<number, string>>({})
const editSort = ref<Record<number, number>>({})

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await listAdminCategories()
    for (const c of items.value) {
      editName.value[c.id] = c.name
      editSort.value[c.id] = c.sort_order
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function addCategory() {
  const name = newName.value.trim()
  if (!name) {
    error.value = '请输入分类名称'
    return
  }
  busyId.value = -1
  error.value = ''
  try {
    await createAdminCategory({ name, sort_order: newSort.value })
    newName.value = ''
    newSort.value = 0
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '创建失败'
  } finally {
    busyId.value = null
  }
}

async function saveCategory(c: CategoryPublic) {
  busyId.value = c.id
  error.value = ''
  try {
    await updateAdminCategory(c.id, {
      name: editName.value[c.id]?.trim(),
      sort_order: editSort.value[c.id],
    })
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    busyId.value = null
  }
}

async function removeCategory(c: CategoryPublic) {
  const ok = await showConfirm({
    title: '删除分类',
    message: `确定删除「${c.name}」？若分类下仍有商品将无法删除。`,
    confirmText: '删除',
    variant: 'danger',
  })
  if (!ok) return
  busyId.value = c.id
  error.value = ''
  try {
    await deleteAdminCategory(c.id)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '删除失败'
  } finally {
    busyId.value = null
  }
}
</script>

<template>
  <section>
    <p class="lede">维护商品分类名称与排序（数字越小越靠前）。</p>
    <p v-if="error" class="ds-form-error">{{ error }}</p>
    <p v-if="loading" class="muted">加载中…</p>

    <div v-else class="panel">
      <h2 class="panel__title ds-label-caps">新增分类</h2>
      <div class="row">
        <input v-model="newName" class="ds-input" placeholder="分类名称" />
        <input v-model.number="newSort" class="ds-input sort" type="number" placeholder="排序" />
        <button type="button" class="ds-btn" :disabled="busyId !== null" @click="addCategory">添加</button>
      </div>

      <h2 class="panel__title ds-label-caps">已有分类</h2>
      <p v-if="!items.length" class="muted">暂无分类</p>
      <ul v-else class="list">
        <li v-for="c in items" :key="c.id" class="item">
          <input v-model="editName[c.id]" class="ds-input" />
          <input v-model.number="editSort[c.id]" class="ds-input sort" type="number" />
          <button type="button" class="ds-btn ds-btn--ghost" :disabled="busyId === c.id" @click="saveCategory(c)">
            保存
          </button>
          <button type="button" class="link-btn danger" :disabled="busyId === c.id" @click="removeCategory(c)">
            删除
          </button>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.lede {
  margin: 0 0 var(--space-lg);
  color: var(--color-body);
  font-size: 14px;
}

.muted {
  color: var(--color-muted);
}

.panel {
  border: 1px solid var(--color-hairline);
  padding: var(--space-lg);
  background: var(--color-surface-card);
}

.panel__title {
  margin: var(--space-lg) 0 var(--space-md);
  color: var(--color-muted);
}

.panel__title:first-child {
  margin-top: 0;
}

.row,
.item {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  align-items: center;
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.sort {
  width: 88px;
}

.link-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-body);
}

.link-btn.danger {
  color: var(--color-m-red);
}
</style>
