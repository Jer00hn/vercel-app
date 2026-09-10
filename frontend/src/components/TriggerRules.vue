<template>
  <div class="bg-white rounded-lg shadow p-6 mt-6">
    <div class="flex justify-between items-center mb-4 flex-wrap gap-2">
      <div>
        <h3 class="text-md font-semibold text-gray-900">🎯 Правила доступа (allowed_triggers)</h3>
        <p class="text-xs text-gray-500 mt-1">
          Управление контентом по подпискам. Файл: {{ file }} • источник: {{ source }}
        </p>
      </div>
      <div class="flex gap-2">
        <button
          @click="addTier"
          class="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
        >
          ➕ Тариф
        </button>
        <button
          @click="handleReset"
          :disabled="saving"
          class="px-3 py-2 text-sm bg-yellow-100 text-yellow-700 rounded-md hover:bg-yellow-200 disabled:opacity-50"
        >
          ↩️ Сбросить
        </button>
        <button
          @click="handleSave"
          :disabled="saving || !dirty"
          class="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ saving ? '💾 Сохранение...' : '💾 Сохранить' }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      <p class="mt-2 text-gray-600">Загрузка правил...</p>
    </div>

    <template v-else>
      <!-- Табы тарифов -->
      <div class="flex gap-1 border-b border-gray-200 mb-4 flex-wrap">
        <button
          v-for="tier in Object.keys(rules)"
          :key="tier"
          @click="activeTier = tier"
          class="px-4 py-2 text-sm font-medium rounded-t-md transition-colors"
          :class="activeTier === tier
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
        >
          {{ tier }}
          <span class="ml-1 text-xs opacity-75">
            {{ rules[tier] === 'ALL' ? '(ALL)' : `(${rules[tier].length})` }}
          </span>
        </button>
      </div>

      <!-- Контент активного тарифа -->
      <div v-if="activeTier && rules[activeTier] === 'ALL'" class="space-y-3">
        <div class="bg-green-50 border border-green-200 rounded-md p-4">
          <p class="text-green-800 font-medium">✅ Полный доступ</p>
          <p class="text-sm text-green-600 mt-1">
            Тарифу «{{ activeTier }}» разрешены все запросы без ограничений.
          </p>
        </div>
        <button
          @click="convertToList(activeTier)"
          class="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
        >
          🔧 Перевести в список правил
        </button>
      </div>

      <div v-else-if="activeTier" class="space-y-3">
        <div class="space-y-2">
          <div
            v-for="(rule, index) in rules[activeTier]"
            :key="index"
            class="flex gap-2 items-center"
          >
            <select
              v-model="rule.method"
              class="px-2 py-2 border border-gray-300 rounded-md text-sm bg-white focus:ring-2 focus:ring-blue-500"
            >
              <option v-for="m in methods" :key="m" :value="m">{{ m }}</option>
            </select>
            <input
              v-model="rule.path"
              placeholder="путь, например index.html?aicc_sid="
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              @change="markDirty"
            />
            <button
              @click="removeRule(activeTier, index)"
              class="px-3 py-2 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200"
              title="Удалить правило"
            >
              🗑️
            </button>
          </div>
        </div>

        <div v-if="rules[activeTier].length === 0" class="text-center py-4 text-gray-500 text-sm">
          Нет правил — тарифу «{{ activeTier }}» ничего не разрешено
        </div>

        <div class="flex gap-2">
          <button
            @click="addRule(activeTier)"
            class="px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
          >
            ➕ Добавить правило
          </button>
          <button
            @click="convertToAll(activeTier)"
            class="px-3 py-2 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200"
          >
            ♾️ Разрешить всё (ALL)
          </button>
          <button
            @click="removeTier(activeTier)"
            class="px-3 py-2 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200 ml-auto"
          >
            🗑️ Удалить тариф
          </button>
        </div>
      </div>

      <p v-if="dirty" class="text-xs text-yellow-600 mt-3">
        ⚠️ Есть несохранённые изменения — не забудьте нажать «Сохранить»
      </p>
    </template>

    <!-- Сообщение -->
    <div
      v-if="message"
      class="mt-4 p-3 rounded-md text-sm"
      :class="messageType"
    >
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { triggersApi } from '../api'

const HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']

const loading = ref(false)
const saving = ref(false)
const dirty = ref(false)
const rules = ref({})
const activeTier = ref('')
const file = ref('')
const source = ref('')
const message = ref('')
const messageType = ref('')

const methods = HTTP_METHODS

// Локальное представление правила: { method, path }
const toLocalRule = (str) => {
  const idx = str.indexOf(':')
  if (idx === -1) return { method: 'GET', path: str }
  return { method: str.slice(0, idx).toUpperCase(), path: str.slice(idx + 1) }
}

const toLocalRules = (data) => {
  const result = {}
  for (const [tier, value] of Object.entries(data || {})) {
    result[tier] = value === 'ALL' ? 'ALL' : (value || []).map(toLocalRule)
  }
  return result
}

// Собираем JSON для отправки: "METHOD:path"
const toPayload = () => {
  const payload = {}
  for (const [tier, value] of Object.entries(rules.value)) {
    if (value === 'ALL') {
      payload[tier] = 'ALL'
    } else {
      payload[tier] = value
        .map(r => `${r.method}:${r.path.trim()}`)
        .filter(r => r.split(':')[1] !== '')
    }
  }
  return payload
}

const showMessage = (text, type = 'bg-green-50 text-green-700') => {
  message.value = text
  messageType.value = type
  setTimeout(() => { message.value = '' }, 5000)
}

const markDirty = () => { dirty.value = true }

const loadTriggers = async () => {
  loading.value = true
  try {
    const { data } = await triggersApi.getTriggers()
    rules.value = toLocalRules(data.rules)
    file.value = data.file || ''
    source.value = data.source || ''
    activeTier.value = Object.keys(rules.value)[0] || ''
    dirty.value = false
  } catch (error) {
    showMessage(`❌ ${error.response?.data?.detail || error.message}`, 'bg-red-50 text-red-700')
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    const { data } = await triggersApi.saveTriggers(toPayload())
    rules.value = toLocalRules(data.rules)
    source.value = 'blob'
    dirty.value = false
    showMessage('✅ Правила сохранены в Blob')
  } catch (error) {
    showMessage(`❌ ${error.response?.data?.detail || error.message}`, 'bg-red-50 text-red-700')
  } finally {
    saving.value = false
  }
}

const handleReset = async () => {
  if (!confirm('Сбросить все правила к значениям по умолчанию? Текущие изменения будут потеряны.')) return
  saving.value = true
  try {
    const { data } = await triggersApi.resetTriggers()
    rules.value = toLocalRules(data.rules)
    source.value = 'blob'
    activeTier.value = Object.keys(rules.value)[0] || ''
    dirty.value = false
    showMessage('↩️ Правила сброшены к значениям по умолчанию')
  } catch (error) {
    showMessage(`❌ ${error.response?.data?.detail || error.message}`, 'bg-red-50 text-red-700')
  } finally {
    saving.value = false
  }
}

const addRule = (tier) => {
  rules.value[tier].push({ method: 'GET', path: '' })
  markDirty()
}

const removeRule = (tier, index) => {
  rules.value[tier].splice(index, 1)
  markDirty()
}

const convertToAll = (tier) => {
  if (!confirm(`Разрешить тарифу «${tier}» все запросы (ALL)?`)) return
  rules.value[tier] = 'ALL'
  markDirty()
}

const convertToList = (tier) => {
  rules.value[tier] = []
  markDirty()
}

const addTier = () => {
  const name = prompt('Название нового тарифа (a-z, 0-9, _, -):', '')
  if (!name) return
  const tier = name.trim().toLowerCase()
  if (!tier) return
  if (rules.value[tier] !== undefined) {
    showMessage(`⚠️ Тариф «${tier}» уже существует`, 'bg-yellow-50 text-yellow-700')
    return
  }
  rules.value[tier] = []
  activeTier.value = tier
  markDirty()
}

const removeTier = (tier) => {
  if (!confirm(`Удалить тариф «${tier}» со всеми правилами?`)) return
  delete rules.value[tier]
  activeTier.value = Object.keys(rules.value)[0] || ''
  markDirty()
}

onMounted(loadTriggers)
</script>
