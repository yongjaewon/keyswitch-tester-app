import { writable } from 'svelte/store';
import { initializeWebSocket } from '../services/api';

export type ConnectionState = {
    is_initializing: boolean;      // True during initial connection attempt
    is_connected: boolean;         // True when WebSocket is connected
    is_data_loaded: boolean;        // True when initial API data is loaded
    reconnect_attempt: number;     // Current reconnection attempt number
    has_reached_max_attempts: boolean; // Whether max reconnection attempts have been reached
    is_first_connection: boolean;  // True until the first connection attempt completes
};

const initial_state: ConnectionState = {
    is_initializing: typeof window !== 'undefined', // Only initialize on client side
    is_connected: false,
    is_data_loaded: false,
    reconnect_attempt: 0,
    has_reached_max_attempts: false,
    is_first_connection: true
};

function createConnectionStore() {
    const { subscribe, set, update } = writable<ConnectionState>(initial_state);

    // Only initialize WebSocket on client side
    if (typeof window !== 'undefined') {
        initializeWebSocket();
    }

    return {
        subscribe,
        
        // Called when WebSocket connects
        setConnected: () => update(state => ({
            ...state,
            is_connected: true,
            reconnect_attempt: 0,
            has_reached_max_attempts: false
        })),

        // Called when WebSocket disconnects
        setDisconnected: () => update(state => ({
            ...state,
            is_connected: false,
            is_first_connection: false // Mark first connection attempt as complete
        })),

        // Called when reconnection attempt starts
        setReconnecting: (attempt: number) => update(state => ({
            ...state,
            reconnect_attempt: attempt,
            is_connected: false,
            is_first_connection: false
        })),

        // Called when max attempts are reached
        setMaxAttemptsReached: () => update(state => ({
            ...state,
            has_reached_max_attempts: true,
            is_connected: false,
            is_first_connection: false
        })),

        // Called when retry button is pressed
        retry: () => {
            update(state => ({
                ...state,
                reconnect_attempt: 0,
                has_reached_max_attempts: false,
                is_initializing: true,
                is_first_connection: true // Reset first connection flag on manual retry
            }));
            initializeWebSocket(true);
        },

        // Called when initial data is loaded
        setDataLoaded: () => {
            update(state => ({
                ...state,
                is_data_loaded: true,
                is_initializing: false,
                is_first_connection: false
            }));
        },

        // Reset to initial state
        reset: () => set(initial_state)
    };
}

export const connectionStore = createConnectionStore(); 