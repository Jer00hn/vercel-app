<template>
  <div class="min-h-screen flex flex-col">
    <!-- Верхний тулбар -->
    <header class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
        <router-link to="/" class="text-lg font-bold text-gray-900">
          Subscription Admin
        </router-link>
        <nav class="flex items-center gap-2">
          <router-link
            to="/"
            class="px-4 py-2 text-sm rounded-md hover:bg-gray-100"
            :class="$route.name === 'home' ? 'text-blue-700 bg-blue-50 font-medium' : 'text-gray-700'"
          >
            Главная
          </router-link>
          <router-link
            to="/admin"
            class="px-4 py-2 text-sm rounded-md hover:bg-gray-100"
            :class="$route.name === 'admin' ? 'text-blue-700 bg-blue-50 font-medium' : 'text-gray-700'"
          >
            Админ-панель
          </router-link>
        </nav>
      </div>
    </header>

    <!-- Содержимое страницы -->
    <main class="flex-1">
      <router-view />
    </main>
  </div>
</template>
