<template>
  <div class="min-h-screen bg-gray-100 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Управление подписками</h1>
          <p class="text-sm text-gray-500">v2.0.0 • Redis Hash</p>
        </div>
        <div class="flex gap-2">
          <!-- Кнопка ручного обновления -->
          <button
            @click="loadData"
            :disabled="loading"
            class="px-4 py-2 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg v-if="!loading" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <svg v-else class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {{ loading ? 'Загрузка...' : 'Обновить' }}
          </button>

          <!-- Кнопка очистки (только для разработки) -->
          <button
            v-if="isDevelopment"
            @click="showClearConfirm = true"
            class="px-4 py-2 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200"
          >
            🗑️ Очистить всё
          </button>
          
          <button
            @click="logout"
            class="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            Выйти
          </button>
        </div>
      </div>

      <!-- Login Form -->
      <div v-if="!isAuthenticated" class="max-w-md mx-auto bg-white rounded-lg shadow p-8 mt-20">
        <h2 class="text-xl font-bold text-center mb-6">Вход в админ-панель</h2>
        <form @submit.prevent="login">
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Admin Token
            </label>
            <input
              v-model="tokenInput"
              type="password"
              placeholder="Введите admin токен"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Войти
          </button>
        </form>
      </div>

      <!-- Dashboard Content -->
      <div v-else>
        <!-- Индикатор последнего обновления -->
        <div class="text-xs text-gray-400 text-right mb-2">
          Последнее обновление: {{ lastUpdated }}
        </div>

        <StatsCards :stats="stats" />
        <SubscriptionForm @added="handleAdd" />
        <SubscriptionList
          :subscriptions="subscriptions"
          :loading="loading"
          @refresh="loadData"
          @extend="showExtendDialog"
          @revoke="handleRevoke"
        />

        <!-- Dialog: Extend -->
        <div v-if="extendDialog.show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div class="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 class="text-lg font-semibold mb-4">Продление подписки</h3>
            <p class="text-sm text-gray-600 mb-4">
              Пользователь: <strong>{{ extendDialog.username }}</strong>
            </p>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Добавить дней
              </label>
              <input
                v-model.number="extendDialog.days"
                type="number"
                min="1"
                max="365"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div class="flex justify-end gap-2">
              <button
                @click="extendDialog.show = false"
                class="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Отмена
              </button>
              <button
                @click="handleExtend"
                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Продлить
              </button>
            </div>
          </div>
        </div>

        <!-- Dialog: Clear All Confirmation -->
        <div v-if="showClearConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div class="bg-white rounded-lg p-6 max-w-md w-full">
            <div class="flex items-center justify-center mb-4">
              <div class="bg-red-100 rounded-full p-3">
                <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            </div>
            <h3 class="text-lg font-semibold text-center mb-2">Очистка всех подписок</h3>
            <p class="text-sm text-gray-600 text-center mb-4">
              Вы уверены? Это действие <strong class="text-red-600">нельзя отменить</strong>.
              Будут удалены все подписки без возможности восстановления.
            </p>
            <div class="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-4">
              <p class="text-xs text-yellow-800">
                ⚠️ Активных подписок: <strong>{{ stats.active || 0 }}</strong>
              </p>
            </div>
            <div class="flex justify-end gap-2">
              <button
                @click="showClearConfirm = false"
                class="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Отмена
              </button>
              <button
                @click="handleClearAll"
                :disabled="clearing"
                class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ clearing ? 'Очистка...' : 'Да, очистить всё' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { subscriptionApi } from '../api'
import StatsCards from '../components/StatsCard.vue'
import SubscriptionForm from '../components/SubscriptionForm.vue'
import SubscriptionList from '../components/SubscriptionList.vue'

const isAuthenticated = ref(false)
const tokenInput = ref('')
const loading = ref(false)
const clearing = ref(false)
const stats = ref({})
const subscriptions = ref([])
const lastUpdated = ref('')
const extendDialog = ref({
  show: false,
  username: '',
  days: 30
})
const showClearConfirm = ref(false)

// Определяем окружение (для показа кнопки очистки)
const isDevelopment = computed(() => {
  return import.meta.env.MODE === 'development' || 
         window.location.hostname === 'localhost' ||
         window.location.hostname === '127.0.0.1'
})

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
}

const updateTimestamp = () => {
  const now = new Date()
  lastUpdated.value = now.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
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

    updateTimestamp()

  } catch (error) {
    console.error('Failed to load data:', error)
    if (error.response?.status === 403) {
      logout()
    }
  } finally {
    loading.value = false
  }
}

const handleAdd = async ({ username, durationDays }) => {
  try {
    await subscriptionApi.addSubscription(username, durationDays)
    await loadData() // Обновляем после добавления
  } catch (error) {
    console.error('Failed to add subscription:', error)
    alert('Ошибка при добавлении подписки')
  }
}

const showExtendDialog = (username) => {
  extendDialog.value = {
    show: true,
    username,
    days: 30
  }
}

const handleExtend = async () => {
  try {
    await subscriptionApi.extendSubscription(
      extendDialog.value.username,
      extendDialog.value.days
    )
    extendDialog.value.show = false
    await loadData() // Обновляем после продления
  } catch (error) {
    console.error('Failed to extend subscription:', error)
    alert('Ошибка при продлении подписки')
  }
}

const handleRevoke = async (username) => {
  if (!confirm(`Вы уверены, что хотите отозвать подписку у ${username}?`)) return

  try {
    await subscriptionApi.revokeSubscription(username)
    await loadData() // Обновляем после отзыва
  } catch (error) {
    console.error('Failed to revoke subscription:', error)
    alert('Ошибка при отзыве подписки')
  }
}

const handleClearAll = async () => {
  clearing.value = true
  try {
    await subscriptionApi.clearAll()
    showClearConfirm.value = false
    await loadData() // Обновляем после очистки
    alert('✅ Все подписки успешно очищены')
  } catch (error) {
    console.error('Failed to clear subscriptions:', error)
    alert('❌ Ошибка при очистке подписок')
  } finally {
    clearing.value = false
  }
}

onMounted(() => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    tokenInput.value = token
    isAuthenticated.value = true
    loadData()
  }
})
</script>
