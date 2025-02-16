import { writable, get } from 'svelte/store';
import { api, initializeWebSocket, onMessage } from '../services/api';

// Types
export interface Station {
  id: number;
  enabled: boolean;
  motor_failures: number;
  switch_failures: number;
  current_cycles: number;
  motor_current: string;
  switch_current: string;
}

export interface AppState {
  current_page: 'test' | 'data' | 'video';
  show_timer_modal: boolean;
  show_settings_modal: boolean;
  show_station_settings_modal: boolean;
  machine_state: 'on' | 'off' | 'disabled';
  cutoff_voltage: number;
  motor_failure_threshold: number;
  switch_failure_threshold: number;
  cycle_limit: number;
  motor_current_threshold: number;
  switch_current_threshold: number;
  cycles_per_minute: number;
  timer_end_time: string | null;
  timer_active: boolean;
  stations: Station[];
  selected_station: Station | null;
  supply_voltage: number;
}

// Initial state
const initialState: AppState = {
  current_page: 'test',
  show_timer_modal: false,
  show_settings_modal: false,
  show_station_settings_modal: false,
  machine_state: 'off',
  cutoff_voltage: 11.1,
  motor_failure_threshold: 10,
  switch_failure_threshold: 10,
  cycle_limit: 100000,
  motor_current_threshold: 100,
  switch_current_threshold: 5,
  cycles_per_minute: 6,
  timer_end_time: null,
  timer_active: false,
  selected_station: null,
  supply_voltage: 13.2,
  stations: [1, 2, 3, 4].map(id => ({
    id,
    enabled: false,
    motor_failures: 0,
    switch_failures: 0,
    current_cycles: 0,
    motor_current: "0.0 A",
    switch_current: "0.0 A"
  }))
};

// Create the store
export const appStore = writable<AppState>(initialState);

// Track pending state changes
let pendingStateChanges: { [key: string]: boolean } = {};

// Register WebSocket message handlers only on the client side
if (typeof window !== 'undefined') {
  onMessage('status_update', (data: {
      supply_voltage: number;
      machine_state: 'on' | 'off' | 'disabled';
      timer_active: boolean;
      timer_end_time: string | null;
      stations: {
          id: number;
          enabled: boolean;
          motor_failures: number;
          switch_failures: number;
          current_cycles: number;
          motor_current: number;
          switch_current: number;
      }[];
  }) => {
      appStore.update(state => {
          // Update stations with new data, but only if not in a modal
          const updatedStations = state.show_timer_modal || state.show_settings_modal || state.show_station_settings_modal
              ? state.stations
              : state.stations.map(station => {
                  const newData = data.stations.find(s => s.id === station.id);
                  if (newData) {
                      // If we have a pending state change for this station, don't update its enabled state
                      const pendingKey = `station_${station.id}`;
                      if (pendingStateChanges[pendingKey]) {
                          return {
                              ...station,
                              motor_failures: newData.motor_failures,
                              switch_failures: newData.switch_failures,
                              current_cycles: newData.current_cycles,
                              motor_current: `${newData.motor_current.toFixed(1)} A`,
                              switch_current: `${newData.switch_current.toFixed(1)} A`
                          };
                      }
                      return {
                          ...station,
                          enabled: newData.enabled,
                          motor_failures: newData.motor_failures,
                          switch_failures: newData.switch_failures,
                          current_cycles: newData.current_cycles,
                          motor_current: `${newData.motor_current.toFixed(1)} A`,
                          switch_current: `${newData.switch_current.toFixed(1)} A`
                      };
                  }
                  return station;
              });

          // Always update timer and system state, regardless of modal state
          return {
              ...state,
              supply_voltage: data.supply_voltage,
              machine_state: data.machine_state,
              timer_active: data.timer_active,
              timer_end_time: data.timer_end_time,
              stations: updatedStations
          };
      });
  });
}

// Store actions
export const actions = {
  toggleRunning: async () => {
    const state = get(appStore);
    // If machine is disabled, do nothing.
    if(state.machine_state === 'disabled') {
      console.error('Machine is disabled. Cannot start.');
      return;
    }
    try {
      if(state.machine_state === 'off') {
        await api.startTest();
      } else if(state.machine_state === 'on') {
        await api.stopTest();
      }
    } catch (error) {
      console.error('Error toggling test state:', error);
    }
  },

  setStationState: async (stationId: number, enabled: boolean) => {
    const pendingKey = `station_${stationId}`;
    pendingStateChanges[pendingKey] = true;
    
    let previousState: Station | undefined;
    
    appStore.update(state => {
      previousState = state.stations.find(s => s.id === stationId);
      return {
        ...state,
        stations: state.stations.map(station => 
          station.id === stationId 
            ? { ...station, enabled: enabled }
            : station
        )
      };
    });

    try {
      await api.setStationState(stationId, enabled);
      // Clear the pending state after a successful update
      delete pendingStateChanges[pendingKey];
    } catch (error) {
      console.error('Error setting station state:', error);
      delete pendingStateChanges[pendingKey];
      // Revert the state if the API call fails
      appStore.update(state => ({
        ...state,
        stations: state.stations.map(station => 
          station.id === stationId && previousState
            ? { ...station, enabled: previousState.enabled }
            : station
        )
      }));
    }
  },

  saveSettings: async (settings: Partial<AppState>) => {
    const previousState = get(appStore);
    
    appStore.update(state => ({ ...state, ...settings }));

    // Call the API
    try {
      // Extract only the system settings fields
      const systemSettings = {
        cutoff_voltage: settings.cutoff_voltage!,
        motor_current_threshold: settings.motor_current_threshold!,
        switch_current_threshold: settings.switch_current_threshold!,
        cycle_limit: settings.cycle_limit!,
        motor_failure_threshold: settings.motor_failure_threshold!,
        switch_failure_threshold: settings.switch_failure_threshold!,
        cycles_per_minute: settings.cycles_per_minute!
      };
      await api.updateSettings(systemSettings);
    } catch (error) {
      console.error('Error saving settings:', error);
      // Revert the state if the API call fails
      appStore.update(() => previousState);
    }
  },

  setTimer: async (hours: number, minutes: number) => {
    try {
      const success = await api.setTimer(hours, minutes);
      if (success) {
        appStore.update(state => ({
          ...state,
          show_timer_modal: false,
          timer_active: hours > 0 || minutes > 0
          // Let the backend's timer_end_time come through WebSocket
        }));
      }
    } catch (error) {
      console.error('Error setting timer:', error);
    }
  },

  clearTimer: async () => {
    try {
      await api.setTimer(0, 0);
      appStore.update(s => ({ ...s, timer_active: false, timer_end_time: null }));
    } catch (error) {
      console.error('Failed to clear timer:', error);
      throw error;
    }
  },

  async updateStationSettings(station_id: number, settings: {
    current_cycles: number;
    motor_failures: number;
    switch_failures: number;
  }) {
    try {
      await api.updateStationSettings(station_id, settings);
      // Update the local store
      appStore.update(state => ({
        ...state,
        stations: state.stations.map(station => 
          station.id === station_id
            ? { ...station, ...settings }
            : station
        ),
        show_station_settings_modal: false,
        selected_station: null
      }));
    } catch (error) {
      console.error('Error updating station settings:', error);
      throw error;
    }
  }
}; 