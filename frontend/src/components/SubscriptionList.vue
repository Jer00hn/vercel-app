<template>
  <div class="bg-white rounded-lg shadow overflow-hidden">
    <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
      <h3 class="text-lg font-semibold">Список подписок</h3>
      <div class="flex gap-2">
        <label class="flex items-center text-sm">
          <input v-model="showExpired" type="checkbox" class="mr-2" />
          Показать истекшие
        </label>
        <button @click="refresh" class="text-sm text-blue-600 hover:text-blue-800">Обновить</button>
      </div>
    </div>

    <div v-if="loading" class="p-6 text-center">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="subscriptions.length === 0" class="p-6 text-center text-gray-500">
      Нет подписок
    </div>

    <div v-else class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Пользователь</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Статус</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Истекает</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Дней осталось</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Действия</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="sub in filteredSubscriptions" :key="sub.username">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ sub.username }}</td>
            <td class="px-6 py-4 whitespace-nowrap"><StatusBadge :status="sub.status" :is-active="sub.is_active" /></td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatDate(sub.expires_at) }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
              <span :class="sub.days_remaining < 7 ? 'text-red-600 font-semibold' : 'text-gray-500'">
                {{ sub.days_remaining }} дн.
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm">
              <button @click="$emit('extend', sub.username)" class="text-blue-600 hover:text-blue-900 mr-3">Продлить</button>
              <button @click="$emit('revoke', sub.username)" class="text-red-600 hover:text-red-900">Отозвать</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({
  subscriptions: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['refresh', 'extend', 'revoke'])

const showExpired = ref(true)

const filteredSubscriptions = computed(() => {
  if (showExpired.value) return props.subscriptions
  return props.subscriptions.filter(s => s.is_active)
})

const formatDate = (timestamp) => {
  if (!timestamp) return '—'
  return new Date(timestamp * 1000).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const refresh = () => emit('refresh')
</script>
