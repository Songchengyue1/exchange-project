<script setup lang="ts">
import { RouterView } from 'vue-router'
import AiChatDrawer from './components/AiChatDrawer.vue'
import AiChatFab from './components/AiChatFab.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
</script>

<template>
  <RouterView />
  <ConfirmDialog />
  <AiChatFab />
  <AiChatDrawer />
</template>
