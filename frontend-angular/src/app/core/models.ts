export type SubscriptionStatusType = 'active' | 'expired' | 'not_found';

export interface SubscriptionRaw {
  expires_at?: number | null;
  is_active: boolean;
  days_remaining?: number;
}

export interface SubscriptionEntry extends SubscriptionRaw {
  username: string;
  status: SubscriptionStatusType;
}

export interface SubscriptionListResponse {
  subscriptions: Record<string, SubscriptionRaw>;
}

export interface SubscriptionStats {
  total?: number;
  active?: number;
  expired?: number;
  expiring_soon?: number;
}

export interface TriggerRule {
  method: string;
  path: string;
}

/** Значение тарифа: 'ALL' — полный доступ, либо список правил "METHOD:path" */
export type TierValue = 'ALL' | TriggerRule[];

export type TriggerRulesMap = Record<string, TierValue>;

export interface TriggersResponse {
  rules: Record<string, 'ALL' | string[]>;
  file?: string;
  source?: string;
}
