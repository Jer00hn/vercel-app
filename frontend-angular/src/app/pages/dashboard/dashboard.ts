import { ChangeDetectionStrategy, Component, computed, inject, signal, isDevMode } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { forkJoin, finalize } from 'rxjs';

import { AuthService } from '../../core/auth.service';
import { SubscriptionApi } from '../../core/subscription-api.service';
import {
  SubscriptionEntry,
  SubscriptionStats
} from '../../core/models';
import { StatsCards } from '../../components/stats-cards/stats-cards';
import { SubscriptionForm } from '../../components/subscription-form/subscription-form';
import { SubscriptionList } from '../../components/subscription-list/subscription-list';
import { TriggerRules } from '../../components/trigger-rules/trigger-rules';

@Component({
  selector: 'app-dashboard',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, StatsCards, SubscriptionForm, SubscriptionList, TriggerRules],
  templateUrl: './dashboard.html'
})
export class DashboardPage {
  private readonly fb = inject(NonNullableFormBuilder);
  readonly auth = inject(AuthService);
  private readonly api = inject(SubscriptionApi);

  readonly loading = signal(false);
  readonly clearing = signal(false);
  readonly stats = signal<SubscriptionStats>({});
  readonly subscriptions = signal<SubscriptionEntry[]>([]);
  readonly lastUpdated = signal('');
  readonly extendDialog = signal({ show: false, username: '', days: 30 });
  readonly showClearConfirm = signal(false);

  readonly activeCount = computed(() => this.stats().active ?? 0);

  readonly loginForm = this.fb.group({
    token: ['', Validators.required]
  });

  // Кнопка очистки — только для разработки (как в Vue-версии)
  readonly isDevelopment =
    isDevMode() || ['localhost', '127.0.0.1'].includes(window.location.hostname);

  constructor() {
    if (this.auth.isAuthenticated()) {
      this.loadData();
    }
  }

  login(): void {
    const token = this.loginForm.getRawValue().token.trim();
    if (!token) {
      return;
    }
    this.auth.setToken(token);
    this.loadData();
  }

  logout(): void {
    this.auth.clear();
    this.loginForm.reset();
  }

  loadData(): void {
    this.loading.set(true);
    forkJoin({
      stats: this.api.getStats(),
      list: this.api.getAll()
    })
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: ({ stats, list }) => {
          this.stats.set(stats);
          const subs = list.subscriptions ?? {};
          this.subscriptions.set(
            Object.entries(subs).map(([username, raw]) => ({
              username,
              ...raw,
              status: raw.is_active ? 'active' : 'expired'
            }))
          );
          this.updateTimestamp();
        },
        error: err => console.error('Failed to load data:', err)
      });
  }

  handleAdd({ username, durationDays }: { username: string; durationDays: number }): void {
    this.api.add(username, durationDays).subscribe({
      next: () => this.loadData(),
      error: err => {
        console.error('Failed to add subscription:', err);
        alert('Ошибка при добавлении подписки');
      }
    });
  }

  showExtendDialog(username: string): void {
    this.extendDialog.set({ show: true, username, days: 30 });
  }

  closeExtend(): void {
    this.extendDialog.update(dialog => ({ ...dialog, show: false }));
  }

  onExtendDaysInput(event: Event): void {
    const days = Number((event.target as HTMLInputElement).value);
    this.extendDialog.update(dialog => ({ ...dialog, days }));
  }

  handleExtend(): void {
    const { username, days } = this.extendDialog();
    this.api.extend(username, days).subscribe({
      next: () => {
        this.closeExtend();
        this.loadData();
      },
      error: err => {
        console.error('Failed to extend subscription:', err);
        alert('Ошибка при продлении подписки');
      }
    });
  }

  handleRevoke(username: string): void {
    if (!confirm(`Вы уверены, что хотите отозвать подписку у ${username}?`)) {
      return;
    }
    this.api.revoke(username).subscribe({
      next: () => this.loadData(),
      error: err => {
        console.error('Failed to revoke subscription:', err);
        alert('Ошибка при отзыве подписки');
      }
    });
  }

  handleClearAll(): void {
    this.clearing.set(true);
    this.api.clearAll().subscribe({
      next: () => {
        this.showClearConfirm.set(false);
        this.loadData();
        alert('✅ Все подписки успешно очищены');
      },
      error: err => {
        console.error('Failed to clear subscriptions:', err);
        alert('❌ Ошибка при очистке подписок');
      },
      complete: () => this.clearing.set(false)
    });
  }

  private updateTimestamp(): void {
    this.lastUpdated.set(
      new Date().toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    );
  }
}
