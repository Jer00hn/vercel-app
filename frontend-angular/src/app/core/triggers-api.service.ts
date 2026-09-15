import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { TriggersResponse, TriggerRulesMap } from './models';

@Injectable({ providedIn: 'root' })
export class TriggersApi {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/triggers';

  getTriggers(): Observable<TriggersResponse> {
    return this.http.get<TriggersResponse>(this.base);
  }

  save(rules: TriggerRulesMap): Observable<TriggersResponse> {
    return this.http.put<TriggersResponse>(`${this.base}/admin`, rules);
  }

  reset(): Observable<TriggersResponse> {
    return this.http.post<TriggersResponse>(`${this.base}/admin/reset`, {});
  }
}
