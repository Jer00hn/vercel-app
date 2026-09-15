import { ChangeDetectionStrategy, Component, signal } from '@angular/core';

interface InstallStep {
  title: string;
  description: string;
}

@Component({
  selector: 'app-home',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './home.html'
})
export class HomePage {
  // Скачивание через backend endpoint /api/download?filename=...
  private readonly fileName = 'installer.desktop';
  private readonly downloadUrl = `/api/download?filename=${encodeURIComponent(this.fileName)}`;

  readonly downloading = signal(false);
  readonly message = signal('');
  readonly messageType = signal('');

  readonly steps: readonly InstallStep[] = [
    {
      title: 'Скачайте установочный файл',
      description:
        'Нажмите кнопку «Скачать» ниже и сохраните файл installer.desktop на рабочем столе вашего компьютера'
    },
    {
      title: 'Разрешите запуск файла',
      description:
        'Двойным кликом по ярлыку запустите установщик. При необходимости разрешите выполнение скачанного файла в настройках безопасности системы.'
    },
    {
      title: 'Запустите установку',
      description:
        'В процессе установки на вашем рабочем столе будет создан ярлык с именем Courser.'
    },
    {
      title: 'Запустите Courser',
      description: 'В дальнейшем для работы программы запускайте ярлык Curser.'
    }
  ];

  async download(): Promise<void> {
    this.downloading.set(true);
    this.message.set('');
    try {
      const response = await fetch(this.downloadUrl);
      if (!response.ok) {
        throw new Error(`Ошибка сервера: ${response.status}`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = this.fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      this.message.set('✅ Загрузка началась');
      this.messageType.set('text-green-600');
    } catch {
      // Endpoint ещё не реализован — показываем заглушку
      this.message.set(
        `⚠️ Файл ${this.fileName} пока недоступен: endpoint для скачивания ещё не реализован.`
      );
      this.messageType.set('text-yellow-600');
    } finally {
      this.downloading.set(false);
    }
  }
}
