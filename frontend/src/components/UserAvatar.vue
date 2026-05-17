<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    src?: string | null
    name: string
    size?: 'sm' | 'md' | 'lg'
    alt?: string
  }>(),
  {
    size: 'md',
    alt: '头像',
  },
)

const initial = computed(() => {
  const s = props.name.trim()
  if (!s) return '?'
  return Array.from(s)[0]
})
</script>

<template>
  <span
    class="user-avatar"
    :class="[`user-avatar--${size}`, { 'user-avatar--initial': !src }]"
    role="img"
    :aria-label="src ? alt : `${name}的头像`"
  >
    <img v-if="src" :src="src" :alt="alt" class="user-avatar__img" />
    <span v-else class="user-avatar__initial" aria-hidden="true">{{ initial }}</span>
  </span>
</template>

<style scoped>
.user-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 50%;
  overflow: hidden;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-card);
}

.user-avatar--sm {
  width: 32px;
  height: 32px;
}

.user-avatar--md {
  width: 48px;
  height: 48px;
}

.user-avatar--lg {
  width: 96px;
  height: 96px;
}

.user-avatar__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.user-avatar--initial {
  background: linear-gradient(
    145deg,
    var(--color-m-blue-light),
    var(--color-m-blue-dark)
  );
  border-color: transparent;
}

.user-avatar__initial {
  font-family: var(--font-display);
  font-weight: 700;
  color: #fff;
  line-height: 1;
  user-select: none;
}

.user-avatar--sm .user-avatar__initial {
  font-size: 14px;
}

.user-avatar--md .user-avatar__initial {
  font-size: 18px;
}

.user-avatar--lg .user-avatar__initial {
  font-size: 36px;
}
</style>
