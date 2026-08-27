<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <h1 class="text-xl font-bold text-gray-900">📋 Subscription Admin</h1>
          </div>
          <div class="flex items-center space-x-4">
            <button 
              @click="activeTab = 'status'"
              :class="activeTab === 'status' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'"
              class="px-4 py-2 rounded-md text-sm font-medium"
            >
              🔍 Check Status
            </button>
            <button 
              @click="activeTab = 'admin'"
              :class="activeTab === 'admin' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'"
              class="px-4 py-2 rounded-md text-sm font-medium"
            >
              🔐 Admin Panel
            </button>
          </div>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <SubscriptionStatus v-if="activeTab === 'status'" />
      <AdminPanel v-else-if="activeTab === 'admin'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SubscriptionStatus from './components/SubscriptionStatus.vue'
import AdminPanel from './components/AdminPanel.vue'

const activeTab = ref('status')
</script>