<script lang="ts">
  import { onMount } from 'svelte';
  import { appStore, actions } from '$lib/stores/appStore';
  import type { AppState } from '$lib/stores/appStore';
  import { formatTime } from '$lib/utils';
  import StationCard from '$lib/components/StationCard.svelte';
  import SettingsModal from '$lib/components/SettingsModal.svelte';
  import TimerModal from '$lib/components/TimerModal.svelte';
  import StationSettingsModal from '$lib/components/StationSettingsModal.svelte';
  import VideoStream from '$lib/components/VideoStream.svelte';
  import { api, initializeWebSocket } from '$lib/services/api';

  let state: AppState;
  let remaining_time: { hours: number; minutes: number; seconds: number } = { hours: 0, minutes: 0, seconds: 0 };
  let timer: ReturnType<typeof setInterval> | null = null;

  // Subscribe to store
  appStore.subscribe((newState: AppState) => {
    state = newState;
    // Always update remaining time when state changes
    updateRemainingTime();
  });

  function updateRemainingTime() {
    if (!state.timer_end_time) {
      remaining_time = { hours: 0, minutes: 0, seconds: 0 };
      if (timer) {
        clearInterval(timer);
        timer = null;
      }
      return;
    }
    
    try {
      // Both endTimeMs and Date.now() are in UTC milliseconds
      const end_time_ms = Date.parse(state.timer_end_time);  // Backend sends UTC with 'Z' suffix
      const now_ms = Date.now();  // UTC milliseconds
      const diff_ms = end_time_ms - now_ms;
      
      if (diff_ms <= 0) {
        remaining_time = { hours: 0, minutes: 0, seconds: 0 };
        if (timer) {
          clearInterval(timer);
          timer = null;
        }
        return;
      }
      
      const hours = Math.floor(diff_ms / (1000 * 60 * 60));
      const minutes = Math.floor((diff_ms % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff_ms % (1000 * 60)) / 1000);
      
      remaining_time = { hours, minutes, seconds };
    } catch (error) {
      console.error('Error updating remaining time:', error);
      remaining_time = { hours: 0, minutes: 0, seconds: 0 };
    }
  }

  // Add animation class for timer indicator
  onMount(() => {
    // Initialize WebSocket connection
    initializeWebSocket();

    // Start timer update interval
    timer = setInterval(() => {
      if (state.timer_active) {
        updateRemainingTime();
      }
    }, 1000);

    // Load initial settings and history from the backend
    (async () => {
      try {
        const [settings, history] = await Promise.all([
          api.getSettings(),
          api.getHistory()
        ]);
        actions.saveSettings(settings);
        appStore.update(s => ({ ...s, history }));
      } catch (error) {
        console.error('Error loading initial data:', error);
      }
    })();

    return () => {
      if (timer) clearInterval(timer);
    };
  });

  // Watch for timer state changes
  $: if (state.timer_active && !timer) {
    timer = setInterval(updateRemainingTime, 1000);
  } else if (!state.timer_active && timer) {
    clearInterval(timer);
    timer = null;
  }

  // Watch for changes in failures and cycles and automatically disable station at thresholds
  $: {
    state.stations.forEach(station => {
      if ((station.motor_failures >= state.motor_failure_threshold || 
           station.switch_failures >= state.switch_failure_threshold ||
           station.current_cycles >= state.cycle_limit) && 
          station.enabled) {
        actions.setStationState(station.id, false);
      }
    });
  }

  // Motor indicator states
  $: motor_indicator_states = [
    { class: "bg-green-500 opacity-100" },             // Solid green
    { class: "bg-red-500 fast-blink" },               // Fast blinking red
    { class: "bg-green-500 slow-blink" },             // Slow blinking green
    { class: "bg-red-500 opacity-100" }               // Solid red
  ];

  // Switch indicator states
  $: switch_indicator_states = [
    { class: "bg-red-500 opacity-100" },              // Solid red
    { class: "bg-green-500 slow-blink" },             // Slow blinking green
    { class: "bg-green-500 opacity-100" },            // Solid green
    { class: "bg-red-500 fast-blink" }                // Fast blinking red
  ];
</script>

<div class="bg-gray-200 dark:bg-gray-900 flex-1 flex">
  <div class="w-full max-w-[1024px] min-w-[340px] mx-auto px-4">
    <div class="h-full">
      {#if state.current_page === 'test'}
        <!-- Main content area -->
        <div class="flex flex-col gap-4">
          <!-- Control buttons for mobile/tablet view -->
          <div class="lg:hidden">
            <!-- Control buttons container with responsive layout -->
            <div class="grid grid-cols-2 gap-4">
              <!-- Start/Stop button -->
              <button type="button" 
                      on:click={actions.toggleRunning}
                      class="text-white font-bold rounded-lg text-2xl min-[400px]:text-3xl sm:text-4xl px-5 h-[70px] sm:h-[92px] transition-all border border-gray-300/90 shadow-md
                      {state.machine_state === 'on' ? 'bg-red-600 active:bg-red-700 dark:bg-red-700 dark:active:bg-red-800' : 
                       state.machine_state === 'off' ? 'bg-green-600 active:bg-green-700 dark:bg-green-700 dark:active:bg-green-800' : 
                       'bg-gray-500 cursor-not-allowed'}">
                {state.machine_state === 'on' ? 'STOP' : state.machine_state === 'off' ? 'START' : 'DISABLED'}
              </button>

              <!-- Timer button -->
              <button type="button" 
                      on:click={() => {
                        if (state.timer_active) {
                          actions.clearTimer();
                        } else {
                          appStore.update((s: AppState) => ({ ...s, show_timer_modal: true }));
                        }
                      }}
                      class="relative text-white bg-gray-600 active:bg-gray-700 font-bold rounded-lg text-xl min-[400px]:text-2xl sm:text-3xl px-5 h-[70px] sm:h-[92px] dark:bg-gray-700 dark:active:bg-gray-800 transition-all flex items-center justify-center gap-2 border border-gray-300/90 shadow-md {state.timer_active ? 'border-4 flash-border border-red-500' : ''}">
                {#if !state.timer_active}
                  Set Timer
                {:else}
                  <svg class="hidden min-[400px]:block w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  {formatTime(remaining_time.hours, remaining_time.minutes, remaining_time.seconds)}
                {/if}
              </button>
            </div>
          </div>

          <!-- Main layout area -->
          <div class="flex-1 flex flex-col lg:flex-row gap-4">
            <!-- Left side - Station cards -->
            <div class="flex-1">
              <div class="grid grid-cols-1 min-[640px]:grid-cols-1 min-[1200px]:grid-cols-1 lg:flex lg:flex-col lg:h-[calc(100vh-7rem)] gap-4">
                {#each state.stations as station, index}
                  <StationCard
                    {station}
                    motor_indicator_state={motor_indicator_states[index].class}
                    switch_indicator_state={switch_indicator_states[index].class}
                    motor_current_threshold={state.motor_current_threshold}
                    switch_current_threshold={state.switch_current_threshold}
                    motor_failure_threshold={state.motor_failure_threshold}
                    switch_failure_threshold={state.switch_failure_threshold}
                  />
                {/each}
              </div>
            </div>

            <!-- Right side - Controls (desktop only) -->
            <div class="hidden lg:flex w-[400px] flex-col gap-[15px] lg:flex-shrink-0">
              <!-- Start/Stop button -->
              <button type="button" 
                      on:click={actions.toggleRunning}
                      class="text-white font-bold rounded-lg text-2xl min-[400px]:text-3xl sm:text-4xl px-5 h-[70px] sm:h-[92px] transition-all border border-gray-300/90 shadow-md
                      {state.machine_state === 'on' ? 'bg-red-600 active:bg-red-700 dark:bg-red-700 dark:active:bg-red-800' : 
                       state.machine_state === 'off' ? 'bg-green-600 active:bg-green-700 dark:bg-green-700 dark:active:bg-green-800' : 
                       'bg-gray-500 cursor-not-allowed'}">
                {state.machine_state === 'on' ? 'STOP' : state.machine_state === 'off' ? 'START' : 'DISABLED'}
              </button>

              <!-- Timer button -->
              <button type="button" 
                      on:click={() => {
                        if (state.timer_active) {
                          actions.clearTimer();
                        } else {
                          appStore.update((s: AppState) => ({ ...s, show_timer_modal: true }));
                        }
                      }}
                      class="relative text-white bg-gray-600 active:bg-gray-700 font-bold rounded-lg text-xl min-[400px]:text-2xl sm:text-3xl px-5 h-[70px] sm:h-[92px] dark:bg-gray-700 dark:active:bg-gray-800 transition-all flex items-center justify-center gap-2 border border-gray-300/90 shadow-md {state.timer_active ? 'border-4 flash-border border-red-500' : ''}">
                {#if !state.timer_end_time}
                  Set Timer
                {:else}
                  <svg class="hidden min-[400px]:block w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  {formatTime(remaining_time.hours, remaining_time.minutes, remaining_time.seconds)}
                {/if}
              </button>

              <!-- Status area - visible only in desktop -->
              <button on:click={() => appStore.update(s => ({ ...s, show_settings_modal: true }))}
                      class="p-4 bg-white border border-gray-300/90 rounded-lg shadow-md dark:bg-gray-800 dark:border-gray-700 h-fit text-left">
                <div class="flex flex-col gap-3">
                  <!-- Status items -->
                  <div class="grid grid-cols-2 gap-4">
                    <!-- Voltage Settings -->
                    <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                      <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">Voltage</h3>
                      <div class="space-y-2">
                        <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                          <div class="flex gap-2">
                            <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            <span>Supply</span>
                          </div>
                          <span>{state.supply_voltage.toFixed(1)} V</span>
                        </div>
                        <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                          <div class="flex gap-2">
                            <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13v-2a1 1 0 00-1-1H4a1 1 0 00-1 1v2a1 1 0 001 1h16a1 1 0 001-1zM12 6v4m0 4v4"/>
                            </svg>
                            <span>Cutoff</span>
                          </div>
                          <span>{state.cutoff_voltage.toFixed(1)} V</span>
                        </div>
                      </div>
                    </div>

                    <!-- Cycle Settings -->
                    <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                      <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">Cycle</h3>
                      <div class="space-y-2">
                        <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                          <div class="flex gap-2">
                            <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            <span>Rate</span>
                          </div>
                          <span>{state.cycles_per_minute} cyc/min</span>
                        </div>
                        <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                          <div class="flex gap-2">
                            <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                              <line x1="4" y1="20" x2="20" y2="4" stroke-width="2" stroke-linecap="round" />
                            </svg>
                            <span>Limit</span>
                          </div>
                          <span>{state.cycle_limit.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>

                    <!-- Motor Settings -->
                    <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                      <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">Motor</h3>
                      <div class="space-y-2">
                        <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                          <div class="flex gap-2">
                            <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <circle cx="12" cy="12" r="9" stroke-width="2" />
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16V8L12 14L16 8V16" />
                            </svg>
                            <span>Current</span>
                          </div>
                          <span>> {state.motor_current_threshold} A</span>
                        </div>
                        <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                          <div class="flex gap-2">
                            <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <rect x="4" y="4" width="16" height="16" rx="2" stroke-width="2" />
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16V8L12 14L16 8V16" />
                            </svg>
                            <span>Failures</span>
                          </div>
                          <span>{state.motor_failure_threshold} max</span>
                        </div>
                      </div>
                    </div>

                    <!-- Switch Settings -->
                    <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                      <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">Switch</h3>
                      <div class="space-y-2">
                        <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                          <div class="flex gap-2">
                            <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <circle cx="12" cy="12" r="9" stroke-width="2" />
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10C15 8 13 8 12 8C11 8 9 8 9 10C9 12 15 12 15 14C15 16 13 16 12 16C11 16 9 16 9 14" />
                            </svg>
                            <span>Current</span>
                          </div>
                          <span>> {state.switch_current_threshold} A</span>
                        </div>
                        <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                          <div class="flex gap-2">
                            <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <rect x="4" y="4" width="16" height="16" rx="2" stroke-width="2" />
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10C15 8 13 8 12 8C11 8 9 8 9 10C9 12 15 12 15 14C15 16 13 16 12 16C11 16 9 16 9 14" />
                            </svg>
                            <span>Failures</span>
                          </div>
                          <span>{state.switch_failure_threshold} max</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </button>
            </div>
          </div>

          <!-- Status area - visible only in mobile/tablet -->
          <div class="lg:hidden mt-auto pb-4">
            <button on:click={() => appStore.update(s => ({ ...s, show_settings_modal: true }))}
                    class="w-full p-4 bg-white border border-gray-300/90 rounded-lg shadow-md dark:bg-gray-800 dark:border-gray-700 h-fit text-left">
              <div class="grid min-[440px]:grid-cols-2 min-[850px]:grid-cols-4 gap-4">
                <!-- Voltage Settings -->
                <div class="bg-gray-100 dark:bg-gray-700/50 rounded-lg p-3">
                  <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">Voltage</h3>
                  <div class="space-y-2">
                    <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                      <div class="flex gap-2">
                        <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <span>Supply</span>
                      </div>
                      <span>{state.supply_voltage.toFixed(1)} V</span>
                    </div>
                    <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                      <div class="flex gap-2">
                        <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13v-2a1 1 0 00-1-1H4a1 1 0 00-1 1v2a1 1 0 001 1h16a1 1 0 001-1zM12 6v4m0 4v4"/>
                        </svg>
                        <span>Cutoff</span>
                      </div>
                      <span>{state.cutoff_voltage.toFixed(1)} V</span>
                    </div>
                  </div>
                </div>

                <!-- Cycle Settings -->
                <div class="bg-gray-100 dark:bg-gray-700/50 rounded-lg p-3">
                  <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">Cycle</h3>
                  <div class="space-y-2">
                    <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                      <div class="flex gap-2">
                        <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        <span>Rate</span>
                      </div>
                      <span>{state.cycles_per_minute} cyc/min</span>
                    </div>
                    <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                      <div class="flex gap-2">
                        <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          <line x1="4" y1="20" x2="20" y2="4" stroke-width="2" stroke-linecap="round" />
                        </svg>
                        <span>Limit</span>
                      </div>
                      <span>{state.cycle_limit.toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                <!-- Motor Settings -->
                <div class="bg-gray-100 dark:bg-gray-700/50 rounded-lg p-3">
                  <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">Motor</h3>
                  <div class="space-y-2">
                    <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                      <div class="flex gap-2">
                        <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <circle cx="12" cy="12" r="9" stroke-width="2" />
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16V8L12 14L16 8V16" />
                        </svg>
                        <span>Current</span>
                      </div>
                      <span>> {state.motor_current_threshold} A</span>
                    </div>
                    <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                      <div class="flex gap-2">
                        <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <rect x="4" y="4" width="16" height="16" rx="2" stroke-width="2" />
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16V8L12 14L16 8V16" />
                        </svg>
                        <span>Failures</span>
                      </div>
                      <span>{state.motor_failure_threshold} max</span>
                    </div>
                  </div>
                </div>

                <!-- Switch Settings -->
                <div class="bg-gray-100 dark:bg-gray-700/50 rounded-lg p-3">
                  <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">Switch</h3>
                  <div class="space-y-2">
                    <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                      <div class="flex gap-2">
                        <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <circle cx="12" cy="12" r="9" stroke-width="2" />
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10C15 8 13 8 12 8C11 8 9 8 9 10C9 12 15 12 15 14C15 16 13 16 12 16C11 16 9 16 9 14" />
                        </svg>
                        <span>Current</span>
                      </div>
                      <span>> {state.switch_current_threshold} A</span>
                    </div>
                    <div class="flex justify-between gap-2 text-gray-600 dark:text-gray-400">
                      <div class="flex gap-2">
                        <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <rect x="4" y="4" width="16" height="16" rx="2" stroke-width="2" />
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10C15 8 13 8 12 8C11 8 9 8 9 10C9 12 15 12 15 14C15 16 13 16 12 16C11 16 9 16 9 14" />
                        </svg>
                        <span>Failures</span>
                      </div>
                      <span>{state.switch_failure_threshold} max</span>
                    </div>
                  </div>
                </div>
              </div>
            </button>
          </div>
        </div>
      {:else if state.current_page === 'data'}
        <!-- Data visualization page -->
        <div class="p-4">
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">System History</h2>
            
            <!-- History Table -->
            <div class="overflow-x-auto">
              <table class="w-full text-left">
                <thead class="bg-gray-50 dark:bg-gray-700/50">
                  <tr>
                    <th class="px-4 py-3 text-sm font-medium text-gray-500 dark:text-gray-400">Time</th>
                    <th class="px-4 py-3 text-sm font-medium text-gray-500 dark:text-gray-400">Station</th>
                    <th class="px-4 py-3 text-sm font-medium text-gray-500 dark:text-gray-400">Event</th>
                    <th class="px-4 py-3 text-sm font-medium text-gray-500 dark:text-gray-400">Details</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                  {#each state.history || [] as entry}
                    <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td class="px-4 py-3 text-sm text-gray-900 dark:text-white whitespace-nowrap">
                        {new Date(entry.timestamp).toLocaleString()}
                      </td>
                      <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">
                        {entry.station_id ? `Station ${entry.station_id}` : 'System'}
                      </td>
                      <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">
                        {entry.event}
                      </td>
                      <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">
                        {entry.details}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      {:else if state.current_page === 'video'}
        <!-- Video feed page -->
        <div class="w-full max-w-4xl mx-auto p-4">
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">Live Camera Feed</h2>
            <VideoStream />
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

{#if state.show_settings_modal}
  <SettingsModal />
{/if}

{#if state.show_timer_modal}
  <TimerModal />
{/if}

{#if state.show_station_settings_modal && state.selected_station}
  <StationSettingsModal station={state.selected_station} />
{/if}

<style>
  /* Remove fixed dimensions and allow responsive behavior */
  :global(html, body) {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
  }

  /* Remove focus outlines globally */
  :global(*:focus) {
    outline: none !important;
  }

  @keyframes flash-border {
    0%, 100% { border-color: rgb(239 68 68); }  /* red-500 */
    50% { border-color: transparent; }          /* completely transparent */
  }

  .flash-border {
    animation: flash-border 1s ease-in-out infinite;
  }
</style>
