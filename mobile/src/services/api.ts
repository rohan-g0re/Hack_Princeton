/**
 * API Service - REST client for backend
 */
import axios, { AxiosInstance } from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api';
import { supabase } from '../config/supabase';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.client.interceptors.request.use(async (config) => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
      }
      return config;
    });
  }

  // Recipe
  async getRecipeIngredients(query: string) {
    const response = await this.client.post(API_ENDPOINTS.RECIPE, { query });
    return response.data;
  }

  // Agents
  async startAgents(sessionId: string, ingredients: any[], platforms: string[]) {
    const response = await this.client.post(API_ENDPOINTS.START_AGENTS, {
      session_id: sessionId,
      ingredients,
      platforms,
    });
    return response.data;
  }

  async getJobStatus(jobId: string) {
    const response = await this.client.get(`${API_ENDPOINTS.JOB_STATUS}/${jobId}/status`);
    return response.data;
  }

  // Cart
  async getCartStatus(sessionId: string) {
    const response = await this.client.get(API_ENDPOINTS.CART_STATUS, {
      params: { session_id: sessionId },
    });
    return response.data;
  }

  async saveCartDiffs(sessionId: string, platform: string, diffs: any[]) {
    const response = await this.client.post(API_ENDPOINTS.CART_DIFFS, {
      session_id: sessionId,
      platform,
      diffs,
    });
    return response.data;
  }

  async applyDiffs(sessionId: string) {
    const response = await this.client.post(API_ENDPOINTS.APPLY_DIFFS, {
      session_id: sessionId,
    });
    return response.data;
  }

  // Checkout
  async checkout(sessionId: string) {
    const response = await this.client.post(API_ENDPOINTS.CHECKOUT, {
      session_id: sessionId,
    });
    return response.data;
  }
}

export const api = new ApiService();

