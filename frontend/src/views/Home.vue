<template>
  <div class="min-h-screen bg-gray-100">
    <div class="max-w-4xl mx-auto px-6 py-12">
      <!-- Заголовок -->
      <div class="text-center mb-10">
        <h1 class="text-3xl font-bold text-gray-900 mb-3">
          Установка программы
        </h1>
        <p class="text-gray-500">
          Следуйте инструкции ниже, чтобы установить и настроить приложение
        </p>
      </div>

      <!-- Инструкция (заглушка) -->
      <div class="bg-white rounded-lg shadow p-8 mb-8">
        <h2 class="text-xl font-semibold text-gray-900 mb-6">Инструкция по установке</h2>
        <ol class="space-y-4">
          <li
            v-for="(step, index) in steps"
            :key="index"
            class="flex items-start gap-4"
          >
            <span class="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center font-semibold text-sm">
              {{ index + 1 }}
            </span>
            <div>
              <h3 class="font-medium text-gray-900">{{ step.title }}</h3>
              <p class="text-sm text-gray-500 mt-1">{{ step.description }}</p>
            </div>
          </li>
        </ol>
      </div>

      <!-- Кнопка скачивания -->
      <div class="text-center">
        <button
          @click="download"
          :disabled="downloading"
          class="px-8 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 mx-auto text-lg font-medium"
        >
          <svg v-if="!downloading" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          <svg v-else class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ downloading ? 'Загрузка...' : 'Скачать installer.desktop' }}
        </button>
        <p v-if="message" class="mt-4 text-sm" :class="messageType">
          {{ message }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// Скачивание через backend endpoint /api/download?filename=...
const FILE_NAME = 'installer.desktop'
const DOWNLOAD_URL = `/api/download?filename=${encodeURIComponent(FILE_NAME)}`

const downloading = ref(false)
const message = ref('')
const messageType = ref('')

const steps = [
  {
    title: 'Скачайте установочный файл',
    description: 'Нажмите кнопку «Скачать» ниже и сохраните файл installer.desktop на рабочем столе вашего компьютера'
  },
  {
    title: 'Разрешите запуск файла',
    description: 'Двоиным кликом по ярлыку запустите установщик.При необходимости разрешите выполнение скачанного файла в настройках безопасности системы.'
  },
  {
    title: 'Запустите установку',
    description: 'В процессе установки на вашем рабочем столе будет создан ярлык с именем Courser.'
  },
  {
    title: 'Запустите Courser',
    description: 'В дальнейшем для работы программы запускайте ярлык Curser.'
  }
]

const showMessage = (text, type) => {
  message.value = text
  messageType.value = type
}

const download = async () => {
  downloading.value = true
  message.value = ''
  try {
    const response = await fetch(DOWNLOAD_URL)
    if (!response.ok) {
      throw new Error(`Ошибка сервера: ${response.status}`)
    }
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = FILE_NAME
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    showMessage('✅ Загрузка началась', 'text-green-600')
  } catch (error) {
    // Endpoint ещё не реализован — показываем заглушку
    showMessage(
      `⚠️ Файл ${FILE_NAME} пока недоступен: endpoint для скачивания ещё не реализован.`,
      'text-yellow-600'
    )
  } finally {
    downloading.value = false
  }
}
</script>
