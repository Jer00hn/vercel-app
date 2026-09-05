<template>
  <div class="min-h-screen bg-gray-100 p-6">
    <div class="max-w-7xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Управление подписками</h1>
          <p class="text-sm text-gray-500">v2.0.0 • Redis Hash</p>
        </div>
        <button @click="logout" class="px-4 py-2 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200">Выйти</button>
      </div>

      <div v-if="!isAuthenticated" class="max-w-md mx-auto bg-white rounded-lg shadow p-8 mt-20">
        <h2 class="text-xl font-bold text-center mb-6">Вход в админ-панель</h2>
        <form @submit.prevent="login">
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">Admin Token</label>
            <input
              v-model="tokenInput"
              type="password"
              placeholder="Введите admin токен"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <button type="submit" class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Войти</button>
        </form>
      </div>

      <div v-else>
        <StatsCards :stats="stats" />
        <SubscriptionForm @added="handleAdd" />
        <SubscriptionList
          :subscriptions="subscriptions"
          :loading="loading"
          @refresh="loadData"
          @extend="showExtendDialog"
          @revoke="handleRevoke"
        />

        <div v-if="extendDialog.show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div class="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 class="text-lg font-semibold mb-4">Продление подписки</h3>
            <p class="text-sm text-gray-600 mb-4">Пользователь: <strong>{{ extendDialog.username }}</strong></p>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">Добавить дней</label>
              <input
                v-model.number="extendDialog.days"
                type="number"
                min="1"
                max="365"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div class="flex justify-end gap-2">
              <button @click="extendDialog.show = false" class="px-4 py-2 text-gray-600 hover:text-gray-800">Отмена</button>
              <button @click="handleExtend" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Продлить</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { subscriptionApi } from '../api'
import StatsCards from '../components/StatsCard.vue'
import SubscriptionForm from '../components/SubscriptionForm.vue'
import SubscriptionList from '../components/SubscriptionList.vue'

const isAuthenticated = ref(false)
const tokenInput = ref('')
const loading = ref(false)
const stats = ref({})
const subscriptions = ref([])
const extendDialog = ref({ show: false, username: '', days: 30 })
let refreshInterval

const login = () => {
  if (tokenInput.value) {
    localStorage.setItem('admin_token', tokenInput.value)
    isAuthenticated.value = true
    loadData()
  }
}

const logout = () => {
  localStorage.removeItem('admin_token')
  isAuthenticated.value = false
  tokenInput.value = ''
  if (refreshInterval) clearInterval(refreshInterval)
}

const loadData = async () => {
  loading.value = true
  try {
    const [statsRes, listRes] = await Promise.all([
      subscriptionApi.getStats(),
      subscriptionApi.getAllSubscriptions({ include_expired: true })
    ])
    stats.value = statsRes.data
    const subs = listRes.data.subscriptions || {}
    subscriptions.value = Object.keys(subs).map(username => ({
      username,
      ...subs[username],
      status: subs[username].is_active ? 'active' : 'expired'
    }))
  } catch (error) {
    console.error('Failed to load data:', error)
    if (error.response?.status === 403) logout()
  } finally {
    loading.value = false
  }
}

const handleAdd = async ({ username, durationDays }) => {
  try {
    await subscriptionApi.addSubscription(username, durationDays)
    await loadData()
  } catch (error) {
    console.error('Failed to add subscription:', error)
    alert('Ошибка при добавлении подписки')
  }
}

const showExtendDialog = (username) => {
  extendDialog.value = { show: true, username, days: 30 }
}

const handleExtend = async () => {
  try {
    await subscriptionApi.extendSubscription(extendDialog.value.username, extendDialog.value.days)
    extendDialog.value.show = false
    await loadData()
  } catch (error) {
    console.error('Failed to extend subscription:', error)
    alert('Ошибка при продлении подписки')
  }
}

const handleRevoke = async (username) => {
  if (!confirm(`Вы уверены, что хотите отозвать подписку у ${username}?`)) return
  try {
    await subscriptionApi.revokeSubscription(username)
    await loadData()
  } catch (error) {
    console.error('Failed to revoke subscription:', error)
    alert('Ошибка при отзыве подписки')
  }
}

onMounted(() => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    tokenInput.value = token
    isAuthenticated.value = true
    loadData()
    refreshInterval = setInterval(() => {
      if (isAuthenticated.value) loadData()
    }, 30000)
  }
})

onBeforeUnmount(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>
