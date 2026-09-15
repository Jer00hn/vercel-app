import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import { SubscriptionStats } from '../../core/models';

interface StatCard {
  label: string;
  value: number;
  valueClass: string;
  iconBgClass: string;
  iconClass: string;
  iconPath: string;
}

@Component({
  selector: 'app-stats-cards',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      @for (card of cards(); track card.label) {
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500">{{ card.label }}</p>
              <p class="text-2xl font-bold" [class]="card.valueClass">{{ card.value }}</p>
            </div>
            <div class="rounded-full p-3" [class]="card.iconBgClass">
              <svg class="w-6 h-6" [class]="card.iconClass" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" [attr.d]="card.iconPath" />
              </svg>
            </div>
          </div>
        </div>
      }
    </div>
  `
})
export class StatsCards {
  readonly stats = input<SubscriptionStats>({});

  readonly cards = computed<StatCard[]>(() => {
    const stats = this.stats();
    return [
      {
        label: 'Всего подписок',
        value: stats.total ?? 0,
        valueClass: '',
        iconBgClass: 'bg-blue-100',
        iconClass: 'text-blue-600',
        iconPath:
          'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10'
      },
      {
        label: 'Активные',
        value: stats.active ?? 0,
        valueClass: 'text-green-600',
        iconBgClass: 'bg-green-100',
        iconClass: 'text-green-600',
        iconPath: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
      },
      {
        label: 'Истекшие',
        value: stats.expired ?? 0,
        valueClass: 'text-red-600',
        iconBgClass: 'bg-red-100',
        iconClass: 'text-red-600',
        iconPath: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
      },
      {
        label: 'Истекают скоро',
        value: stats.expiring_soon ?? 0,
        valueClass: 'text-yellow-600',
        iconBgClass: 'bg-yellow-100',
        iconClass: 'text-yellow-600',
        iconPath: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
      }
    ];
  });
}
