<template>
  <div class="bg-white rounded-lg shadow p-6 mb-6">
    <h3 class="text-lg font-semibold mb-4">Добавить подписку</h3>
    <div class="flex flex-wrap gap-4">
      <div class="flex-1 min-w-[200px]">
        <label class="block text-sm font-medium text-gray-700 mb-1">Имя пользователя</label>
        <input
          v-model="username"
          type="text"
          placeholder="username"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          :disabled="loading"
        />
      </div>
      <div class="flex-1 min-w-[150px]">
        <label class="block text-sm font-medium text-gray-700 mb-1">Дней</label>
        <input
          v-model.number="durationDays"
          type="number"
          min="1"
          max="3650"
          placeholder="30"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          :disabled="loading"
        />
      </div>
      <div class="flex items-end">
        <button
          @click="handleSubmit"
          :disabled="loading || !username || !durationDays"
          class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Добавление...' : 'Добавить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineEmits } from 'vue'

const emit = defineEmits(['added'])

const username = ref('')
const durationDays = ref(30)
const loading = ref(false)

const handleSubmit = async () => {
  if (!username.value || !durationDays.value) return
  loading.value = true
  try {
    emit('added', {
      username: username.value,
      durationDays: durationDays.value
    })
    username.value = ''
    durationDays.value = 30
  } finally {
    loading.value = false
  }
}
</script>
