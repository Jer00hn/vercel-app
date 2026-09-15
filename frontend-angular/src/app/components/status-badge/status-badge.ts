import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import { SubscriptionStatusType } from '../../core/models';

@Component({
  selector: 'app-status-badge',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" [class]="badgeClass()">
      <span class="w-1.5 h-1.5 mr-1.5 rounded-full" [class]="dotClass()" aria-hidden="true"></span>
      {{ label() }}
    </span>
  `
})
export class StatusBadge {
  readonly status = input<SubscriptionStatusType>('not_found');

  readonly label = computed(() => {
    switch (this.status()) {
      case 'active':
        return 'Активна';
      case 'expired':
        return 'Истекла';
      default:
        return 'Не найдена';
    }
  });

  readonly badgeClass = computed(() => {
    switch (this.status()) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'expired':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  });

  readonly dotClass = computed(() => {
    switch (this.status()) {
      case 'active':
        return 'bg-green-400';
      case 'expired':
        return 'bg-red-400';
      default:
        return 'bg-gray-400';
    }
  });
}
