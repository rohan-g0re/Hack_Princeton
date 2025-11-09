import { Ingredient, PlatformSummary, JobStatus } from './types';

const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new APIError(
      response.status,
      errorData.detail || `HTTP ${response.status}`
    );
  }
  
  return response.json();
}

export const api = {
  async getRecipeIngredients(recipeName: string) {
    return apiFetch<{ ingredients: Ingredient[] }>('/recipes/ingredients', {
      method: 'POST',
      body: JSON.stringify({ recipe_name: recipeName }),
    });
  },
  
  async saveShoppingList(items: Ingredient[]) {
    return apiFetch<{ saved: boolean; count: number }>('/shopping-list', {
      method: 'POST',
      body: JSON.stringify({ items }),
    });
  },
  
  async startDriver() {
    return apiFetch<{ job_id: string }>('/run-driver', {
      method: 'POST',
    });
  },
  
  async getDriverStatus(jobId: string) {
    return apiFetch<{
      job_id: string;
      status: JobStatus;
      cart_count: number;
      knot_api_count: number;
      message?: string;
    }>(`/run-driver/status?job_id=${jobId}`);
  },
  
  async getComparison(jobId: string) {
    return apiFetch<{ job_id: string; platforms: PlatformSummary[] }>(
      `/comparison/${jobId}`
    );
  },
};

export { APIError };

