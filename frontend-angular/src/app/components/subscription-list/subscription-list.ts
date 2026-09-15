import { ChangeDetectionStrategy, Component, computed, input, output, signal } from '@angular/core';

import { SubscriptionEntry } from '../../core/models';
import { StatusBadge } from '../status-badge/status-badge';

@Component({
  selector: 'app-subscription-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [StatusBadge],
  templateUrl: './subscription-list.html'
})
export class SubscriptionList {
  readonly subscriptions = input<SubscriptionEntry[]>([]);
  readonly loading = input(false);

  readonly refresh = output<void>();
  readonly extend = output<string>();
  readonly revoke = output<string>();

  readonly showExpired = signal(true);
  readonly filtered = computed(() => {
    const subs = this.subscriptions();
    return this.showExpired() ? subs : subs.filter(s => s.is_active);
  });

  toggleExpired(event: Event): void {
    this.showExpired.set((event.target as HTMLInputElement).checked);
  }

  formatDate(timestamp: number | null | undefined): string {
    if (!timestamp) {
      return '—';
    }
    return new Date(timestamp * 1000).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}
