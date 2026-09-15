import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { SubscriptionListResponse, SubscriptionStats } from './models';

@Injectable({ providedIn: 'root' })
export class SubscriptionApi {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/subscription';

  getStats(): Observable<SubscriptionStats> {
    return this.http.get<SubscriptionStats>(`${this.base}/admin/stats`);
  }

  getAll(): Observable<SubscriptionListResponse> {
    return this.http.get<SubscriptionListResponse>(`${this.base}/admin/list`, {
      params: { include_expired: true }
    });
  }

  add(username: string, durationDays: number): Observable<unknown> {
    return this.http.post(`${this.base}/admin/add`, null, {
      params: { username, duration_days: durationDays }
    });
  }

  extend(username: string, extraDays: number): Observable<unknown> {
    return this.http.put(`${this.base}/admin/extend`, null, {
      params: { username, extra_days: extraDays }
    });
  }

  revoke(username: string): Observable<unknown> {
    return this.http.delete(`${this.base}/admin/revoke`, {
      params: { username }
    });
  }

  clearAll(): Observable<unknown> {
    return this.http.delete(`${this.base}/admin/clear`);
  }
}
