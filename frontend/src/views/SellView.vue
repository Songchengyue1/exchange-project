<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listCategories } from '../api/categories'
import { createProduct, getProduct, updateProduct, uploadProductImages } from '../api/products'
import { showConfirm } from '../composables/useConfirm'
import type { CategoryPublic } from '../types/product'

const route = useRoute()
const router = useRouter()

const categories = ref<CategoryPublic[]>([])
const loadingCats = ref(true)

const editId = computed(() => {
  const e = route.query.edit
  if (e == null || e === '') return null
  const n = Number(e)
  return Number.isFinite(n) ? n : null
})

const categoryId = ref<number | null>(null)
const title = ref('')
const description = ref('')
const price = ref<number>(0)
const condition = ref('excellent')
const tradeType = ref('pickup')
const stock = ref(1)
const files = ref<File[]>([])
const previews = ref<{ file: File; url: string }[]>([])
const fileInput = ref<HTMLInputElement | null>(null)

function revokePreviews() {
  for (const p of previews.value) {
    URL.revokeObjectURL(p.url)
  }
  previews.value = []
}

function syncPreviews(list: File[]) {
  revokePreviews()
  previews.value = list.map((file) => ({ file, url: URL.createObjectURL(file) }))
  files.value = list
}

const saving = ref(false)
const error = ref('')
const msg = ref('')

async function loadCats() {
  loadingCats.value = true
  try {
    categories.value = await listCategories()
    if (!categoryId.value && categories.value.length) {
      categoryId.value = categories.value[0].id
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '分类加载失败'
  } finally {
    loadingCats.value = false
  }
}

async function loadProductForEdit() {
  const pid = editId.value
  if (pid == null) return
  error.value = ''
  try {
    const p = await getProduct(pid)
    categoryId.value = p.category_id
    title.value = p.title
    description.value = p.description
    price.value = p.price
    condition.value = p.condition
    tradeType.value = p.trade_type
    stock.value = p.stock
  } catch (e) {
    error.value = e instanceof Error ? e.message : '无法加载商品'
  }
}

onMounted(async () => {
  await loadCats()
  await loadProductForEdit()
})

onUnmounted(revokePreviews)

watch(editId, () => {
  void loadProductForEdit()
})

function onFiles(e: Event) {
  const input = e.target as HTMLInputElement
  const picked = input.files ? Array.from(input.files) : []
  const merged = [...files.value, ...picked].slice(0, 6)
  syncPreviews(merged)
}

function removePreview(index: number) {
  const next = files.value.filter((_, i) => i !== index)
  syncPreviews(next)
  if (fileInput.value && !next.length) fileInput.value.value = ''
}

async function submit() {
  msg.value = ''
  error.value = ''
  if (!categoryId.value) {
    error.value = '请选择分类'
    return
  }
  if (!title.value.trim()) {
    error.value = '请填写标题'
    return
  }
  if (!price.value || price.value <= 0) {
    error.value = '价格须大于 0'
    return
  }

  const isEdit = editId.value != null
  const ok = await showConfirm({
    title: isEdit ? '保存修改' : '发布商品',
    message: isEdit
      ? '确定要保存对该商品的修改吗？修改标题、价格、描述等核心信息将重新进入待审核；仅调整库存则保持当前上架状态。'
      : '确定要提交该商品吗？提交后将进入待审核，通过后方可在前台展示。',
    confirmText: isEdit ? '保存' : '提交',
  })
  if (!ok) return

  saving.value = true
  try {
    const body = {
      category_id: categoryId.value,
      title: title.value.trim(),
      description: description.value,
      price: price.value,
      condition: condition.value,
      trade_type: tradeType.value,
      stock: stock.value,
    }
    let pid: number
    if (editId.value != null) {
      const p = await updateProduct(editId.value, body)
      pid = p.id
      msg.value = p.status === 'pending' ? '已保存修改，待审核' : '已保存修改'
    } else {
      const p = await createProduct(body)
      pid = p.id
      msg.value = '已创建，待审核'
    }
    if (files.value.length) {
      await uploadProductImages(pid, files.value)
      revokePreviews()
      files.value = []
      if (fileInput.value) fileInput.value.value = ''
      msg.value += '；图片已上传'
    }
    if (editId.value == null) {
      await router.push({ path: '/my-products' })
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '提交失败'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="wrap page-narrow">
    <p class="eyebrow ds-label-caps">Listing</p>
    <h1 class="title">{{ editId != null ? '编辑商品' : '发布商品' }}</h1>
    <p class="lede">提交后进入待审核；驳回后可修改并重新提交。图片最多 6 张，单张 ≤ 2MB。</p>

    <p v-if="msg" class="msg">{{ msg }}</p>
    <p v-if="error" class="ds-form-error">{{ error }}</p>

    <form class="form" @submit.prevent="submit">
      <div class="ds-field">
        <label class="ds-label" for="cat">分类</label>
        <select id="cat" v-model.number="categoryId" class="ds-input" :disabled="loadingCats">
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
      <div class="ds-field">
        <label class="ds-label" for="t">标题</label>
        <input id="t" v-model="title" class="ds-input" maxlength="200" required />
      </div>
      <div class="ds-field">
        <label class="ds-label" for="d">描述</label>
        <textarea id="d" v-model="description" class="ds-textarea" maxlength="20000" />
      </div>
      <div class="ds-field">
        <label class="ds-label" for="p">价格（元）</label>
        <input id="p" v-model.number="price" class="ds-input" type="number" min="0" step="0.01" required />
      </div>
      <div class="ds-field">
        <label class="ds-label" for="cnd">成色</label>
        <select id="cnd" v-model="condition" class="ds-input">
          <option value="brand_new">全新</option>
          <option value="like_new">99 新</option>
          <option value="excellent">成色优</option>
          <option value="good">良好</option>
          <option value="fair">一般</option>
        </select>
      </div>
      <div class="ds-field">
        <label class="ds-label" for="tt">交易方式</label>
        <select id="tt" v-model="tradeType" class="ds-input">
          <option value="pickup">自提</option>
          <option value="shipping">邮寄</option>
          <option value="both">自提 / 邮寄</option>
        </select>
      </div>
      <div class="ds-field">
        <label class="ds-label" for="st">库存</label>
        <input id="st" v-model.number="stock" class="ds-input" type="number" min="1" step="1" required />
      </div>
      <div class="ds-field">
        <label class="ds-label" for="img">商品图片（可选，可多选）</label>
        <input
          id="img"
          ref="fileInput"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          @change="onFiles"
        />
        <p v-if="files.length" class="hint">已选 {{ files.length }} 张（最多 6 张）</p>
        <ul v-if="previews.length" class="previews">
          <li v-for="(p, i) in previews" :key="p.url" class="preview">
            <img :src="p.url" :alt="p.file.name" class="preview__img" />
            <button
              type="button"
              class="preview__remove"
              aria-label="移除图片"
              title="移除"
              @click="removePreview(i)"
            >
              ×
            </button>
          </li>
        </ul>
      </div>
      <button type="submit" class="ds-btn" :disabled="saving">{{ saving ? '提交中…' : '提交' }}</button>
    </form>
  </section>
</template>

<style scoped>
.wrap {
  padding-top: var(--space-section);
  padding-bottom: var(--space-section);
}

.eyebrow {
  margin: 0 0 var(--space-md);
  color: var(--color-muted);
}

.title {
  margin: 0 0 var(--space-sm);
  font-family: var(--font-display);
  font-size: clamp(26px, 3.5vw, 36px);
  font-weight: 700;
  color: var(--color-on-dark);
}

.lede {
  margin: 0 0 var(--space-xl);
  font-size: 16px;
  font-weight: 300;
  color: var(--color-body);
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.msg {
  margin: 0 0 var(--space-md);
  color: var(--color-success);
  font-size: 14px;
  font-weight: 300;
}

.hint {
  margin: var(--space-xs) 0 0;
  font-size: 13px;
  color: var(--color-muted);
}

.previews {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin: var(--space-md) 0 0;
  padding: 0;
  list-style: none;
}

.preview {
  position: relative;
  width: 88px;
  height: 88px;
  flex-shrink: 0;
  border: 1px solid var(--color-hairline);
  border-radius: 10px;
  overflow: hidden;
  background: var(--color-surface-soft);
}

.preview__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.preview__remove {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.65);
  color: #fff;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color var(--duration-fast) ease;
}

.preview__remove:hover {
  background: var(--color-m-red);
}
</style>
