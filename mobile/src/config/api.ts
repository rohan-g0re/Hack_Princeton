/**
 * API Configuration
 */

// For local development, use your machine's IP address
// Find it with: ipconfig (Windows) or ifconfig (Mac/Linux)
export const API_BASE_URL = process.env.API_BASE_URL || 'http://192.168.1.100:8000';

export const API_ENDPOINTS = {
  // Auth
  SIGNUP: '/auth/signup',
  SIGNIN: '/auth/signin',
  ME: '/auth/me',
  
  // Recipe
  RECIPE: '/api/recipe',
  
  // Agents
  START_AGENTS: '/api/start-agents',
  JOB_STATUS: '/api/job',
  
  // Cart
  CART_STATUS: '/api/cart-status',
  CART_DIFFS: '/api/cart-diffs',
  APPLY_DIFFS: '/api/apply-diffs',
  
  // Checkout
  CHECKOUT: '/api/checkout',
  
  // WebSocket
  WS_AGENT_PROGRESS: '/ws/agent-progress',
};

// WebSocket URL (convert http to ws)
export const WS_BASE_URL = API_BASE_URL.replace('http', 'ws');

