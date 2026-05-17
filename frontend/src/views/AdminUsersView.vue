<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listAdminAuditLogs, listAdminUsers, patchAdminUser, resetAdminUserPassword } from '../api/admin'
import { ADMIN_AUDIT_ACTION_LABELS } from '../constants/adminLabels'
import { showConfirm } from '../composables/useConfirm'
import type { AdminAuditLogItem, AdminUserItem } from '../types/admin'

const users = ref<AdminUserItem[]>([])
const logs = ref<AdminAuditLogItem[]>([])
const loading = ref(true)
const error = ref('')
const busyId = ref<number | null>(null)
const passwordDraft = ref<Record<number, string>>({})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [u, l] = await Promise.all([listAdminUsers(), listAdminAuditLogs()])
    users.value = u
    logs.value = l
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function toggleDisabled(u: AdminUserItem) {
  const enabling = u.is_disabled
  const ok = await showConfirm({
    title: enabling ? '启用用户' : '禁用用户',
    message: `确定${enabling ? '启用' : '禁用'}用户「${u.nickname}」（${u.username}）？`,
    confirmText: enabling ? '启用' : '禁用',
    variant: enabling ? 'default' : 'danger',
  })
  if (!ok) return
  busyId.value = u.id
  error.value = ''
  try {
    await patchAdminUser(u.id, { is_disabled: !u.is_disabled })
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    busyId.value = null
  }
}

async function resetPassword(u: AdminUserItem) {
  const pwd = (passwordDraft.value[u.id] || '').trim()
  if (pwd.length < 6) {
    error.value = '新密码至少 6 位'
    return
  }
  const ok = await showConfirm({
    title: '重置密码',
    message: `确定重置用户「${u.username}」的密码？`,
    confirmText: '重置',
    variant: 'danger',
  })
  if (!ok) return
  busyId.value = u.id
  error.value = ''
  try {
    await resetAdminUserPassword(u.id, pwd)
    passwordDraft.value[u.id] = ''
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '重置失败'
  } finally {
    busyId.value = null
  }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN')
}
</script>

<template>
  <section>
    <p class="lede">禁用/启用账号、重置密码；敏感操作会写入审计日志。</p>
    <p v-if="error" class="ds-form-error">{{ error }}</p>
    <p v-if="loading" class="muted">加载中…</p>

    <template v-else>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>用户</th>
              <th>角色</th>
              <th>状态</th>
              <th>信誉</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>
                <strong>{{ u.nickname }}</strong>
                <span class="sub">@{{ u.username }}</span>
              </td>
              <td>{{ u.role === 'admin' ? '管理员' : '普通用户' }}</td>
              <td>
                <span :class="u.is_disabled ? 'badge badge--off' : 'badge badge--on'">
                  {{ u.is_disabled ? '已禁用' : '正常' }}
                </span>
              </td>
              <td>{{ u.rating_avg ?? '—' }}</td>
              <td class="actions">
                <button
                  v-if="u.role !== 'admin'"
                  type="button"
                  class="link-btn"
                  :disabled="busyId === u.id"
                  @click="toggleDisabled(u)"
                >
                  {{ u.is_disabled ? '启用' : '禁用' }}
                </button>
                <input
                  v-model="passwordDraft[u.id]"
                  class="ds-input pwd"
                  type="password"
                  placeholder="新密码"
                  autocomplete="new-password"
                />
                <button
                  type="button"
                  class="ds-btn ds-btn--ghost compact"
                  :disabled="busyId === u.id"
                  @click="resetPassword(u)"
                >
                  重置密码
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <h2 class="section-title ds-label-caps">审计日志（最近 50 条）</h2>
      <ul class="log-list">
        <li v-for="log in logs" :key="log.id" class="log-item">
          <span class="log-time">{{ formatTime(log.created_at) }}</span>
          <span class="log-action">{{ ADMIN_AUDIT_ACTION_LABELS[log.action] ?? log.action }}</span>
          <span class="log-target">{{ log.target_type }} #{{ log.target_id }}</span>
          <span v-if="log.detail" class="log-detail">{{ log.detail }}</span>
          <span class="log-admin">by {{ log.admin_username }}</span>
        </li>
        <li v-if="!logs.length" class="muted">暂无审计记录</li>
      </ul>
    </template>
  </section>
</template>

<style scoped>
.lede {
  margin: 0 0 var(--space-lg);
  font-size: 14px;
  color: var(--color-body);
}

.muted {
  color: var(--color-muted);
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-card);
  margin-bottom: var(--space-xl);
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.table th,
.table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-hairline);
}

.sub {
  display: block;
  font-size: 12px;
  color: var(--color-muted);
}

.badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
}

.badge--on {
  background: rgba(0, 120, 80, 0.12);
  color: #007850;
}

.badge--off {
  background: rgba(226, 39, 24, 0.1);
  color: var(--color-m-red);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.pwd {
  width: 120px;
}

.compact {
  padding: 0 12px;
  height: 36px;
}

.link-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-on-dark);
  font-size: 13px;
}

.section-title {
  margin: 0 0 var(--space-md);
  color: var(--color-muted);
}

.log-list {
  list-style: none;
  padding: 0;
  margin: 0;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-soft);
}

.log-item {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-hairline);
  font-size: 13px;
}

.log-time {
  color: var(--color-muted);
  min-width: 140px;
}

.log-action {
  font-weight: 600;
  color: var(--color-on-dark);
}

.log-detail {
  color: var(--color-body);
}

.log-admin {
  margin-left: auto;
  color: var(--color-muted);
}
</style>
