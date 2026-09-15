import { ChangeDetectionStrategy, Component, output, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({
  selector: 'app-subscription-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule],
  template: `
    <div class="bg-white rounded-lg shadow p-6 mb-6">
      <h3 class="text-lg font-semibold mb-4">Добавить подписку</h3>
      <form [formGroup]="form" (ngSubmit)="submit()">
        <div class="flex flex-wrap gap-4">
          <div class="flex-1 min-w-[200px]">
            <label for="sub-username" class="block text-sm font-medium text-gray-700 mb-1">
              Имя пользователя
            </label>
            <input
              id="sub-username"
              type="text"
              formControlName="username"
              placeholder="username"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div class="flex-1 min-w-[150px]">
            <label for="sub-days" class="block text-sm font-medium text-gray-700 mb-1">Дней</label>
            <input
              id="sub-days"
              type="number"
              formControlName="durationDays"
              min="1"
              max="3650"
              placeholder="30"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div class="flex items-end">
            <button
              type="submit"
              [disabled]="form.invalid"
              class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
              Добавить
            </button>
          </div>
        </div>
      </form>
    </div>
  `
})
export class SubscriptionForm {
  readonly added = output<{ username: string; durationDays: number }>();

  readonly form = new FormGroup({
    username: new FormControl('', { nonNullable: true, validators: Validators.required }),
    durationDays: new FormControl(30, {
      nonNullable: true,
      validators: [Validators.required, Validators.min(1), Validators.max(3650)]
    })
  });

  submit(): void {
    if (this.form.invalid) {
      return;
    }
    const { username, durationDays } = this.form.getRawValue();
    this.added.emit({ username: username.trim(), durationDays });
    this.form.reset({ username: '', durationDays: 30 });
  }
}
