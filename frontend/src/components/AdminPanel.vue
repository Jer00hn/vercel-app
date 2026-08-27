<template>
  <div class="space-y-6">
    <!-- Admin Token -->
    <div class="bg-white rounded-lg shadow p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">🔐 Admin Authentication</h2>
      <div class="flex gap-4">
        <input 
          v-model="adminToken"
          type="password"
          placeholder="Введите admin token..."
          class="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button 
          @click="saveToken"
          class="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
        >
          💾 Save Token
        </button>
      </div>
      <p class="text-sm text-gray-500 mt-2">Token хранится в localStorage</p>
    </div>

    <!-- Добавление подписки -->
    <div class="bg-white rounded-lg shadow p-6">
      <h3 class="text-md font-semibold text-gray-900 mb-4">➕ Добавить подписку</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <input 
          v-model="addForm.username" 
          placeholder="Username" 
          class="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <input 
          v-model.number="addForm.duration_days" 
          type="number" 
          placeholder="Дней" 
          class="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button 
          @click="handleAddSubscription" 
          class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Добавить
        </button>
      </div>
    </div>

    <!-- Продление подписки -->
    <div class="bg-white rounded-lg shadow p-6">
      <h3 class="text-md font-semibold text-gray-900 mb-4">⏰ Продлить подписку</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <input 
          v-model="extendForm.username" 
          placeholder="Username" 
          class="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <input 
          v-model.number="extendForm.extra_days" 
          type="number" 
          placeholder="Дней" 
          class="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button 
          @click="handleExtendSubscription" 
          class="px-6 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors"
        >
          Продлить
        </button>
      </div>
    </div>

    <!-- Отзыв подписки -->
    <div class="bg-white rounded-lg shadow p-6">
      <h3 class="text-md font-semibold text-gray-900 mb-4">🗑️ Отозвать подписку</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <input 
          v-model="revokeForm.username" 
          placeholder="Username" 
          class="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button 
          @click="handleRevokeSubscription" 
          class="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Отозвать
        </button>
      </div>
    </div>

    <!-- Список всех подписок -->
    <div class="bg-white rounded-lg shadow p-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-md font-semibold text-gray-900">📋 Список всех подписок</h3>
        <button 
          @click="loadSubscriptions" 
          :disabled="loading"
          class="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors disabled:opacity-50"
        >
          {{ loading ? '⏳ Загрузка...' : '🔄 Загрузить список' }}
        </button>
      </div>
      
      <div v-if="loading" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        <p class="mt-2 text-gray-600">Загрузка...</p>
      </div>
      
      <div v-else-if="Object.keys(subscriptions).length > 0" class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Username
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Expires At
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Days Left
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="(sub, username) in subscriptions" :key="username">
              <td class="px-6 py-4 text-sm font-medium text-gray-900">
                {{ username }}
              </td>
              <td class="px-6 py-4 text-sm text-gray-500">
                {{ formatDate(sub.expires_at) }}
              </td>
              <td class="px-6 py-4 text-sm">
                <span 
                  :class="sub.is_active ? 'text-green-600' : 'text-red-600'"
                  class="font-medium"
                >
                  {{ sub.is_active ? '✅ Active' : '❌ Expired' }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-gray-500">
                {{ sub.is_active ? sub.days_remaining : '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div v-else-if="!loading" class="text-center py-8 text-gray-500">
        Нет активных подписок
      </div>
    </div>

    <!-- Сообщения -->
    <div v-if="message" class="p-4 rounded-md" :class="messageType">
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { 
  addSubscription as apiAddSubscription,
  extendSubscription as apiExtendSubscription,
  revokeSubscription as apiRevokeSubscription,
  listSubscriptions as apiListSubscriptions
} from '../api/client'

// ============ STATE ============
const adminToken = ref(localStorage.getItem('admin_token') || '')
const loading = ref(false)
const subscriptions = ref({})
const message = ref('')
const messageType = ref('')

const addForm = reactive({ 
  username: '', 
  duration_days: 30 
})

const extendForm = reactive({ 
  username: '', 
  extra_days: 30 
})

const revokeForm = reactive({ 
  username: '' 
})

// ============ HELPERS ============
const showMessage = (text, type) => {
  message.value = text
  messageType.value = type
  setTimeout(() => { 
    message.value = '' 
  }, 5000)
}

const getHeaders = () => ({
  headers: { 
    'Authorization': `Bearer ${adminToken.value}` 
  }
})

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

// ============ ACTIONS ============
const saveToken = () => {
  if (!adminToken.value.trim()) {
    showMessage('⚠️ Введите token', 'bg-yellow-50 text-yellow-700')
    return
  }
  localStorage.setItem('admin_token', adminToken.value)
  showMessage('✅ Token сохранен', 'bg-green-50 text-green-700')
}

const handleAddSubscription = async () => {
  if (!addForm.username.trim()) {
    showMessage('⚠️ Введите username', 'bg-yellow-50 text-yellow-700')
    return
  }
  
  if (!addForm.duration_days || addForm.duration_days <= 0) {
    showMessage('⚠️ Введите корректное количество дней', 'bg-yellow-50 text-yellow-700')
    return
  }

  if (!adminToken.value) {
    showMessage('⚠️ Сначала сохраните admin token', 'bg-yellow-50 text-yellow-700')
    return
  }

  try {
    await apiAddSubscription(
      addForm.username.trim(), 
      addForm.duration_days, 
      getHeaders()
    )
    showMessage(
      `✅ Подписка для ${addForm.username} добавлена на ${addForm.duration_days} дней`, 
      'bg-green-50 text-green-700'
    )
    addForm.username = ''
    addForm.duration_days = 30
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.message
    showMessage(`❌ ${errorMsg}`, 'bg-red-50 text-red-700')
  }
}

const handleExtendSubscription = async () => {
  if (!extendForm.username.trim()) {
    showMessage('⚠️ Введите username', 'bg-yellow-50 text-yellow-700')
    return
  }
  
  if (!extendForm.extra_days || extendForm.extra_days <= 0) {
    showMessage('⚠️ Введите корректное количество дней', 'bg-yellow-50 text-yellow-700')
    return
  }

  if (!adminToken.value) {
    showMessage('⚠️ Сначала сохраните admin token', 'bg-yellow-50 text-yellow-700')
    return
  }

  try {
    await apiExtendSubscription(
      extendForm.username.trim(), 
      extendForm.extra_days, 
      getHeaders()
    )
    showMessage(
      `✅ Подписка для ${extendForm.username} продлена на ${extendForm.extra_days} дней`, 
      'bg-green-50 text-green-700'
    )
    extendForm.username = ''
    extendForm.extra_days = 30
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.message
    showMessage(`❌ ${errorMsg}`, 'bg-red-50 text-red-700')
  }
}

const handleRevokeSubscription = async () => {
  if (!revokeForm.username.trim()) {
    showMessage('⚠️ Введите username', 'bg-yellow-50 text-yellow-700')
    return
  }

  if (!adminToken.value) {
    showMessage('⚠️ Сначала сохраните admin token', 'bg-yellow-50 text-yellow-700')
    return
  }

  if (!confirm(`Вы уверены, что хотите отозвать подписку для ${revokeForm.username}?`)) {
    return
  }

  try {
    await apiRevokeSubscription(revokeForm.username.trim(), getHeaders())
    showMessage(
      `✅ Подписка для ${revokeForm.username} отозвана`, 
      'bg-green-50 text-green-700'
    )
    revokeForm.username = ''
    // Обновляем список после удаления
    await loadSubscriptions()
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.message
    showMessage(`❌ ${errorMsg}`, 'bg-red-50 text-red-700')
  }
}

const loadSubscriptions = async () => {
  if (!adminToken.value) {
    showMessage('⚠️ Сначала сохраните admin token', 'bg-yellow-50 text-yellow-700')
    return
  }

  loading.value = true
  try {
    const data = await apiListSubscriptions(getHeaders())
    subscriptions.value = data.subscriptions || {}
    
    const total = Object.keys(subscriptions.value).length
    if (total > 0) {
      showMessage(`✅ Загружено ${total} подписок`, 'bg-green-50 text-green-700')
    }
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.message
    showMessage(`❌ ${errorMsg}`, 'bg-red-50 text-red-700')
    subscriptions.value = {}
  } finally {
    loading.value = false
  }
}
</script>