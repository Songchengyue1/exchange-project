import { reactive } from 'vue'

export type ConfirmVariant = 'default' | 'danger'

export interface ConfirmOptions {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  variant?: ConfirmVariant
}

const state = reactive({
  visible: false,
  title: '请确认',
  message: '',
  confirmText: '确定',
  cancelText: '取消',
  variant: 'default' as ConfirmVariant,
})

let pending: ((value: boolean) => void) | null = null

function close(result: boolean) {
  state.visible = false
  const resolve = pending
  pending = null
  resolve?.(result)
}

/** 打开二次确认弹窗，用户点确定 resolve(true)，取消或遮罩 resolve(false) */
export function showConfirm(options: ConfirmOptions): Promise<boolean> {
  if (state.visible && pending) {
    pending(false)
    pending = null
  }

  state.title = options.title ?? '请确认'
  state.message = options.message
  state.confirmText = options.confirmText ?? '确定'
  state.cancelText = options.cancelText ?? '取消'
  state.variant = options.variant ?? 'default'
  state.visible = true

  return new Promise<boolean>((resolve) => {
    pending = resolve
  })
}

export function acceptConfirm() {
  close(true)
}

export function dismissConfirm() {
  close(false)
}

export function useConfirmState() {
  return state
}
