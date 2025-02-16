import type { AppState } from '../stores/appStore';
import { connectionStore } from '../stores/connectionStore';

// Types for API requests and responses
interface SystemSettings {
  cutoff_voltage: number;
  motor_current_threshold: number;
  switch_current_threshold: number;
  cycle_limit: number;
  motor_failure_threshold: number;
  switch_failure_threshold: number;
  cycles_per_minute: number;
}

interface Station {
  id: number;
  enabled: boolean;
  motor_failures: number;
  switch_failures: number;
  current_cycles: number;
  motor_current: number;
  switch_current: number;
}

interface SystemState {
  machine_state: string;
  supply_voltage: number;
  timer_active: boolean;
  timer_end_time: string | null;  // UTC ISO string
  stations: Station[];
}

// WebSocket connection
let ws: WebSocket | null = null;
let reconnect_attempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 2000;

// Event handlers type
type MessageHandler = (data: any) => void;

// Message handlers for different event types
const message_handlers: { [key: string]: MessageHandler[] } = {};

// Initialize WebSocket connection
export async function initializeWebSocket(is_manual_retry: boolean = false) {
  // Only initialize WebSocket on the client side
  if (typeof window === 'undefined') return;
  if (ws) return;

  if (is_manual_retry) {
    reconnect_attempts = 0;
  }

  ws = new WebSocket(import.meta.env.VITE_WS_URL);

  ws.onopen = async () => {
    console.log('WebSocket connected');
    connectionStore.setConnected();
    reconnect_attempts = 0;
    
    // Load initial data
    try {
      const [settings, status] = await Promise.all([
        api.getSettings(),
        api.getStatus()
      ]);
      // Once we have initial data, mark as loaded
      connectionStore.setDataLoaded();
    } catch (error) {
      console.error('Error loading initial data:', error);
      connectionStore.setDisconnected();
      ws?.close();
    }
  };

  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data);
      const handlers = message_handlers[message.type];
      if (handlers) {
        handlers.forEach(handler => handler(message.data));
      }
    } catch (e) {
      console.error('Error processing WebSocket message:', e);
    }
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
    ws = null;
    connectionStore.setDisconnected();

    // Try to reconnect if we haven't exceeded max attempts
    if (reconnect_attempts < MAX_RECONNECT_ATTEMPTS) {
        reconnect_attempts++;
        connectionStore.setReconnecting(reconnect_attempts);
        console.log(`Reconnecting... Attempt ${reconnect_attempts}`);
        setTimeout(initializeWebSocket, RECONNECT_DELAY);
    } else {
        console.error('Max reconnection attempts reached');
        connectionStore.setMaxAttemptsReached();
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    connectionStore.setDisconnected();
  };
}

// Register message handler
export function onMessage(type: string, handler: MessageHandler) {
  // Only register handlers on the client side
  if (typeof window === 'undefined') {
    return () => {}; // Return no-op cleanup function for SSR
  }
  
  if (!message_handlers[type]) {
    message_handlers[type] = [];
  }
  message_handlers[type].push(handler);
  return () => {
    message_handlers[type] = message_handlers[type].filter(h => h !== handler);
  };
}

// Send message to server
export function sendMessage(type: string, data: any) {
  if (!ws || typeof window === 'undefined') return;
  
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type, data }));
  } else {
    console.error('WebSocket is not connected');
  }
}

// API endpoints
const API_BASE_URL = `${import.meta.env.VITE_API_URL}/api`;

// HTTP request helper
async function fetchWithError(url: string, options: RequestInit = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error_data = await response.json().catch(() => null);
      throw new Error(error_data?.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

// API functions
export const api = {
  // Authentication
  async authenticate(pin: string): Promise<boolean> {
    const response = await fetch(`${API_BASE_URL}/auth?pin=${pin}`, {
      credentials: 'include'
    });
    const data = await response.json();
    return data.success;
  },

  // Settings
  async getSettings(): Promise<Partial<AppState>> {
    const response = await fetch(`${API_BASE_URL}/settings`, {
      credentials: 'include'
    });
    return response.json();
  },

  async updateSettings(settings: Partial<AppState>): Promise<boolean> {
    const response = await fetch(`${API_BASE_URL}/settings`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    });
    const data = await response.json();
    return data.success;
  },

  // System status
  async getStatus(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/status`, {
      credentials: 'include'
    });
    return response.json();
  },

  // Test control
  async startTest(): Promise<boolean> {
    const response = await fetch(`${API_BASE_URL}/test/start`, {
      method: 'POST',
      credentials: 'include'
    });
    const data = await response.json();
    return data.success;
  },

  async stopTest(): Promise<boolean> {
    const response = await fetch(`${API_BASE_URL}/test/stop`, {
      method: 'POST',
      credentials: 'include'
    });
    const data = await response.json();
    return data.success;
  },

  // Station control
  async setStationState(station_id: number, enabled: boolean): Promise<void> {
    await fetchWithError(`${API_BASE_URL}/station/${station_id}/state`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ enabled })
    });
  },

  // Add new function for updating station settings
  async updateStationSettings(station_id: number, settings: { 
    current_cycles: number;
    motor_failures: number;
    switch_failures: number;
  }): Promise<void> {
    await fetchWithError(`${API_BASE_URL}/station/${station_id}/settings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings)
    });
  },

  // Timer
  async setTimer(hours: number, minutes: number): Promise<boolean> {
    const response = await fetchWithError(`${API_BASE_URL}/timer`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ hours, minutes })
    });
    return response.success;
  },
}; 
