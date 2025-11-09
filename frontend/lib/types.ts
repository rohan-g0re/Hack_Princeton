export interface Ingredient {
  id: string;
  name: string;
  quantity: number;
  unit?: string | null;
}

export interface PlatformSummary {
  name: string;
  logo: string;
  items: ItemSummary[];
  subtotal: number;
  tax: number;
  total: number;
  date: string;
  best_deal: boolean;
}

export interface ItemSummary {
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export type Stage = 'search' | 'edit' | 'results';
export type JobStatus = 'pending' | 'running' | 'success' | 'error';

