import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="min-h-screen flex flex-col">
      <header class="bg-white shadow">
        <div class="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <a routerLink="/" class="text-lg font-bold text-gray-900">Subscription Admin</a>
          <nav class="flex items-center gap-2">
            <a
              routerLink="/"
              routerLinkActive="text-blue-700 bg-blue-50 font-medium"
              [routerLinkActiveOptions]="{ exact: true }"
              ariaCurrentWhenActive="page"
              class="px-4 py-2 text-sm rounded-md hover:bg-gray-100 text-gray-700"
            >
              Главная
            </a>
            <a
              routerLink="/admin"
              routerLinkActive="text-blue-700 bg-blue-50 font-medium"
              ariaCurrentWhenActive="page"
              class="px-4 py-2 text-sm rounded-md hover:bg-gray-100 text-gray-700"
            >
              Админ-панель
            </a>
          </nav>
        </div>
      </header>

      <main class="flex-1">
        <router-outlet />
      </main>
    </div>
  `
})
export class App {}
