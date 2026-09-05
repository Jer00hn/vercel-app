<template>
  <span :class="[
    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
    status === 'active' ? 'bg-green-100 text-green-800' :
    status === 'expired' ? 'bg-red-100 text-red-800' :
    'bg-gray-100 text-gray-800'
  ]">
    <span class="w-1.5 h-1.5 mr-1.5 rounded-full" :class="[
      status === 'active' ? 'bg-green-400' :
      status === 'expired' ? 'bg-red-400' :
      'bg-gray-400'
    ]"></span>
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  isActive: Boolean,
  status: {
    type: String,
    default: 'not_found'
  }
})

const label = computed(() => {
  if (props.status === 'active') return 'Активна'
  if (props.status === 'expired') return 'Истекла'
  return 'Не найдена'
})

const status = computed(() => {
  if (props.status === 'active') return 'active'
  if (props.status === 'expired') return 'expired'
  return 'not_found'
})
</script>
