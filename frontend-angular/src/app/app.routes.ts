import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/home/home').then(m => m.HomePage),
    title: 'Subscription Admin — Установка'
  },
  {
    path: 'admin',
    loadComponent: () => import('./pages/dashboard/dashboard').then(m => m.DashboardPage),
    title: 'Subscription Admin — Админ-панель'
  },
  { path: '**', redirectTo: '' }
];
