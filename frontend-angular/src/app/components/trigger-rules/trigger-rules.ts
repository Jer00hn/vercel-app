import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';

import { TriggersApi } from '../../core/triggers-api.service';
import { TriggerRule, TriggerRulesMap, TriggersResponse } from '../../core/models';

const HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'];

@Component({
  selector: 'app-trigger-rules',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './trigger-rules.html'
})
export class TriggerRules {
  private readonly triggersApi = inject(TriggersApi);

  readonly methods = HTTP_METHODS;

  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly dirty = signal(false);
  readonly rules = signal<TriggerRulesMap>({});
  readonly activeTier = signal('');
  readonly file = signal('');
  readonly source = signal('');
  readonly message = signal('');
  readonly messageType = signal('');

  readonly tiers = computed(() => Object.keys(this.rules()));
  readonly isActiveTierAll = computed(() => this.rules()[this.activeTier()] === 'ALL');
  readonly activeRuleList = computed<TriggerRule[]>(() => {
    const value = this.rules()[this.activeTier()];
    return Array.isArray(value) ? value : [];
  });

  private messageTimer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    this.loadTriggers();
  }

  // ============ Преобразования ============

  /** Строка "METHOD:path" -> локальное правило */
  private toLocalRule(str: string): TriggerRule {
    const idx = str.indexOf(':');
    if (idx === -1) {
      return { method: 'GET', path: str };
    }
    return { method: str.slice(0, idx).toUpperCase(), path: str.slice(idx + 1) };
  }

  private toLocalRules(data: TriggersResponse['rules']): TriggerRulesMap {
    const result: TriggerRulesMap = {};
    for (const [tier, value] of Object.entries(data ?? {})) {
      result[tier] = value === 'ALL' ? 'ALL' : (value ?? []).map(r => this.toLocalRule(r));
    }
    return result;
  }

  /** Собирает JSON для отправки: "METHOD:path" */
  private toPayload(): TriggerRulesMap {
    const payload: TriggerRulesMap = {};
    for (const [tier, value] of Object.entries(this.rules())) {
      if (value === 'ALL') {
        payload[tier] = 'ALL';
      } else {
        payload[tier] = value
          .map(r => `${r.method}:${r.path.trim()}`)
          .filter(r => r.split(':')[1] !== '')
          .map(r => this.toLocalRule(r));
      }
    }
    return payload;
  }

  tierLabel(tier: string): string {
    const value = this.rules()[tier];
    return value === 'ALL' ? '(ALL)' : `(${Array.isArray(value) ? value.length : 0})`;
  }

  // ============ Состояние ============

  private showMessage(text: string, type = 'bg-green-50 text-green-700'): void {
    if (this.messageTimer) {
      clearTimeout(this.messageTimer);
    }
    this.message.set(text);
    this.messageType.set(type);
    this.messageTimer = setTimeout(() => this.message.set(''), 5000);
  }

  private applyResponse(data: TriggersResponse, keepActiveTier = false): void {
    this.rules.set(this.toLocalRules(data.rules));
    if (!keepActiveTier) {
      this.activeTier.set(Object.keys(this.rules())[0] ?? '');
    }
    this.dirty.set(false);
  }

  private loadTriggers(): void {
    this.loading.set(true);
    this.triggersApi.getTriggers().subscribe({
      next: data => {
        this.file.set(data.file ?? '');
        this.source.set(data.source ?? '');
        this.applyResponse(data);
        this.loading.set(false);
      },
      error: err => {
        this.showMessage(`❌ ${err.error?.detail ?? err.message}`, 'bg-red-50 text-red-700');
        this.loading.set(false);
      }
    });
  }

  // ============ Действия ============

  handleSave(): void {
    this.saving.set(true);
    this.triggersApi.save(this.toPayload()).subscribe({
      next: data => {
        const activeTier = this.activeTier();
        this.source.set('blob');
        this.applyResponse(data, true);
        if (!this.rules()[activeTier]) {
          this.activeTier.set(Object.keys(this.rules())[0] ?? '');
        }
        this.showMessage('✅ Правила сохранены в Blob');
        this.saving.set(false);
      },
      error: err => {
        this.showMessage(`❌ ${err.error?.detail ?? err.message}`, 'bg-red-50 text-red-700');
        this.saving.set(false);
      }
    });
  }

  handleReset(): void {
    if (
      !confirm('Сбросить все правила к значениям по умолчанию? Текущие изменения будут потеряны.')
    ) {
      return;
    }
    this.saving.set(true);
    this.triggersApi.reset().subscribe({
      next: data => {
        this.source.set('blob');
        this.applyResponse(data);
        this.showMessage('↩️ Правила сброшены к значениям по умолчанию');
        this.saving.set(false);
      },
      error: err => {
        this.showMessage(`❌ ${err.error?.detail ?? err.message}`, 'bg-red-50 text-red-700');
        this.saving.set(false);
      }
    });
  }

  // ============ Редактирование правил (иммутабельно, для zoneless) ============

  addRule(): void {
    const tier = this.activeTier();
    this.rules.update(rules => {
      const list = Array.isArray(rules[tier]) ? [...(rules[tier] as TriggerRule[])] : [];
      list.push({ method: 'GET', path: '' });
      return { ...rules, [tier]: list };
    });
    this.dirty.set(true);
  }

  removeRule(index: number): void {
    const tier = this.activeTier();
    this.rules.update(rules => {
      const list = (rules[tier] as TriggerRule[]).filter((_, i) => i !== index);
      return { ...rules, [tier]: list };
    });
    this.dirty.set(true);
  }

  updateMethod(index: number, event: Event): void {
    this.patchRule(index, { method: (event.target as HTMLSelectElement).value });
  }

  updatePath(index: number, event: Event): void {
    this.patchRule(index, { path: (event.target as HTMLInputElement).value });
  }

  private patchRule(index: number, patch: Partial<TriggerRule>): void {
    const tier = this.activeTier();
    this.rules.update(rules => {
      const list = (rules[tier] as TriggerRule[]).map((rule, i) =>
        i === index ? { ...rule, ...patch } : rule
      );
      return { ...rules, [tier]: list };
    });
    this.dirty.set(true);
  }

  convertToAll(): void {
    const tier = this.activeTier();
    if (!confirm(`Разрешить тарифу «${tier}» все запросы (ALL)?`)) {
      return;
    }
    this.rules.update(rules => ({ ...rules, [tier]: 'ALL' }));
    this.dirty.set(true);
  }

  convertToList(): void {
    const tier = this.activeTier();
    this.rules.update(rules => ({ ...rules, [tier]: [] }));
    this.dirty.set(true);
  }

  addTier(): void {
    const name = prompt('Название нового тарифа (a-z, 0-9, _, -):', '');
    if (!name) {
      return;
    }
    const tier = name.trim().toLowerCase();
    if (!tier) {
      return;
    }
    if (this.rules()[tier] !== undefined) {
      this.showMessage(`⚠️ Тариф «${tier}» уже существует`, 'bg-yellow-50 text-yellow-700');
      return;
    }
    this.rules.update(rules => ({ ...rules, [tier]: [] }));
    this.activeTier.set(tier);
    this.dirty.set(true);
  }

  removeTier(): void {
    const tier = this.activeTier();
    if (!confirm(`Удалить тариф «${tier}» со всеми правилами?`)) {
      return;
    }
    this.rules.update(rules => {
      const next = { ...rules };
      delete next[tier];
      return next;
    });
    this.activeTier.set(Object.keys(this.rules())[0] ?? '');
    this.dirty.set(true);
  }
}
