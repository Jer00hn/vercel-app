<template>
  <div class="bg-white rounded-lg shadow p-6">
    <h2 class="text-lg font-semibold text-gray-900 mb-4">🔍 Проверка статуса подписки</h2>
    
    <div class="flex gap-4">
      <input 
        v-model="username"
        type="text"
        placeholder="Введите username..."
        class="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
        @keyup.enter="checkStatus"
      />
      <button 
        @click="checkStatus"
        :disabled="loading"
        class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
      >
        {{ loading ? '⏳ Checking...' : 'Check' }}
      </button>
    </div>

    <div v-if="result" class="mt-6 p-4 rounded-md" :class="resultClass">
      <div class="flex items-center justify-between">
        <div>
          <p class="font-medium">{{ result.username }}</p>
          <p class="text-sm" :class="result.is_active ? 'text-green-700' : 'text-red-700'">
            Status: <strong>{{ result.status }}</strong>
          </p>
          <p v-if="result.expires_at" class="text-sm text-gray-600">
            Expires: {{ formatDate(result.expires_at) }}
          </p>
          <p v-if="result.days_remaining > 0" class="text-sm text-gray-600">
            {{ result.days_remaining }} days remaining
          </p>
        </div>
        <div class="text-4xl">
          {{ result.is_active ? '✅' : '❌' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { checkSubscription } from '../api/client'

const username = ref('')
const loading = ref(false)
const result = ref(null)

const resultClass = computed(() => {
  if (!result.value) return ''
  return result.value.is_active 
    ? 'bg-green-50 border border-green-200'
    : 'bg-red-50 border border-red-200'
})

const checkStatus = async () => {
  if (!username.value.trim()) return
  
  loading.value = true
  try {
    result.value = await checkSubscription(username.value)
  } catch (error) {
    result.value = {
      username: username.value,
      status: 'error',
      is_active: false,
      error: error.message
    }
  } finally {
    loading.value = false
  }
}

const formatDate = (timestamp) => {
  if (!timestamp) return '—'
  return new Date(timestamp * 1000).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>