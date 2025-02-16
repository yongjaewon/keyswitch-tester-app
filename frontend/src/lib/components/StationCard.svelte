<script lang="ts">
  import { appStore, actions } from '../stores/appStore';
  import type { Station } from '../stores/appStore';
  import { getCurrentBadgeClass, getFailureBadgeClass } from '../utils';

  export let station: Station;
  export let motor_indicator_state: string;
  export let switch_indicator_state: string;
  export let motor_current_threshold: number;
  export let switch_current_threshold: number;
  export let motor_failure_threshold: number;
  export let switch_failure_threshold: number;
</script>

<div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-300/90 dark:border-gray-700 shadow-md lg:h-[114px] lg:flex-none">
  <div class="p-[14px] h-full flex">
    <!-- Main content area (clickable) -->
    <div class="flex-1">
      <!-- Mobile layout (2x2 grid) for screens below lg -->
      <div class="lg:hidden">
        <!-- Top row: Station ID and toggle switch -->
        <div class="grid grid-cols-2 gap-4 mb-2">
          <!-- Top Left: Station ID -->
          <div class="flex items-center">
            <h3 class="text-2xl font-bold text-gray-900 dark:text-white whitespace-nowrap">Station {station.id}</h3>
            <button 
              class="ml-2 p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              on:click={() => {
                appStore.update(s => ({ 
                  ...s, 
                  show_station_settings_modal: true,
                  selected_station: station
                }));
              }}
            >
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
          <!-- Top Right: Toggle switch -->
          <div class="flex justify-end items-center">
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" 
                     checked={station.enabled}
                     on:change={(e) => actions.setStationState(station.id, e.currentTarget.checked)}
                     class="sr-only peer">
              <div class="w-[72px] h-10 bg-gray-300 border border-gray-300 rounded-full peer dark:bg-gray-600 dark:border-gray-600 peer-checked:after:translate-x-8 peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:border-gray-300 after:rounded-full after:h-9 after:w-9 after:transition-all peer-checked:bg-green-600 peer-checked:border-green-600"></div>
            </label>
          </div>
        </div>

        <!-- Middle: Cycle count -->
        <div class="flex flex-col items-center mb-3 py-2 bg-gray-100 dark:bg-gray-700/50 rounded-lg">
          <div class="flex items-baseline gap-2">
            <div class="text-3xl font-bold text-gray-900 dark:text-white">
              {station.current_cycles.toLocaleString()}
            </div>
            <div class="text-base font-medium text-gray-500 dark:text-gray-400">
              Cycles
            </div>
          </div>
        </div>

        <!-- Bottom row: Status cards -->
        <div class="grid grid-cols-2 gap-4">
          <!-- Bottom Left: Motor Status -->
          <div class="flex flex-col gap-2 p-3 bg-gray-100 dark:bg-gray-700/50 rounded-lg">
            <div class="flex items-center justify-center relative">
              <span class="text-base font-semibold text-gray-700 dark:text-gray-300">Motor</span>
              <div class="absolute right-0 w-2 h-2 rounded-full {motor_indicator_state}"></div>
            </div>
            <div class="text-base font-bold text-center px-2 py-0.5 rounded-full {getCurrentBadgeClass(station.motor_current, motor_current_threshold)}">
              {station.motor_current}
            </div>
            <div class="text-base font-bold text-center px-2 py-0.5 rounded-full {getFailureBadgeClass(station.motor_failures, motor_failure_threshold)}">
              {station.motor_failures} Fails
            </div>
          </div>

          <!-- Bottom Right: Switch Status -->
          <div class="flex flex-col gap-2 p-3 bg-gray-100 dark:bg-gray-700/50 rounded-lg">
            <div class="flex items-center justify-center relative">
              <span class="text-base font-semibold text-gray-700 dark:text-gray-300">Switch</span>
              <div class="absolute right-0 w-2 h-2 rounded-full {switch_indicator_state}"></div>
            </div>
            <div class="text-base font-bold text-center px-2 py-0.5 rounded-full {getCurrentBadgeClass(station.switch_current, switch_current_threshold)}">
              {station.switch_current}
            </div>
            <div class="text-base font-bold text-center px-2 py-0.5 rounded-full {getFailureBadgeClass(station.switch_failures, switch_failure_threshold)}">
              {station.switch_failures} Fails
            </div>
          </div>
        </div>
      </div>

      <!-- Desktop layout (original horizontal layout) -->
      <div class="hidden lg:flex items-center h-full">
        <!-- Station info -->
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <h3 class="text-2xl font-bold text-gray-900 dark:text-white">Station {station.id}</h3>
            <button 
              class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              on:click={() => {
                appStore.update(s => ({ 
                  ...s, 
                  show_station_settings_modal: true,
                  selected_station: station
                }));
              }}
            >
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
          <div class="flex items-baseline gap-2 mt-2">
            <div class="text-3xl font-bold text-gray-900 dark:text-white">
              {station.current_cycles.toLocaleString()}
            </div>
            <div class="text-base font-medium text-gray-500 dark:text-gray-400 tracking-wide">
              Cycles
            </div>
          </div>
        </div>

        <!-- Failure indicators -->
        <div class="flex items-center">
          <div class="flex-1 flex flex-col items-center px-2">
            <div class="relative flex items-center h-6">
              <span class="text-base font-semibold text-gray-700 dark:text-gray-300">Motor</span>
              <div class="absolute -right-3 w-2 h-2 rounded-full {motor_indicator_state}"></div>
            </div>
            <div class="flex flex-col items-center w-[120px]">
              <span class="text-base font-bold px-2 py-0.5 rounded-full {getCurrentBadgeClass(station.motor_current, motor_current_threshold)}">
                {station.motor_current}
              </span>
              <span class="text-base font-bold px-2 py-0.5 rounded-full mt-1 {getFailureBadgeClass(station.motor_failures, motor_failure_threshold)}">
                {station.motor_failures} Fails
              </span>
            </div>
          </div>

          <div class="h-16 w-px bg-gray-400 dark:bg-gray-500"></div>

          <div class="flex-1 flex flex-col items-center px-2">
            <div class="relative flex items-center h-6">
              <span class="text-base font-semibold text-gray-700 dark:text-gray-300">Switch</span>
              <div class="absolute -right-3 w-2 h-2 rounded-full {switch_indicator_state}"></div>
            </div>
            <div class="flex flex-col items-center w-[120px]">
              <span class="text-base font-bold px-2 py-0.5 rounded-full {getCurrentBadgeClass(station.switch_current, switch_current_threshold)}">
                {station.switch_current}
              </span>
              <span class="text-base font-bold px-2 py-0.5 rounded-full mt-1 {getFailureBadgeClass(station.switch_failures, switch_failure_threshold)}">
                {station.switch_failures} Fails
              </span>
            </div>
          </div>

          <div class="h-16 w-px bg-gray-400 dark:bg-gray-500"></div>
        </div>
      </div>
    </div>

    <!-- Toggle switch area (desktop only) -->
    <div class="hidden lg:flex items-center lg:ml-5 lg:mr-2">
      <label class="relative inline-flex items-center cursor-pointer">
        <input type="checkbox" 
               checked={station.enabled}
               on:change={(e) => actions.setStationState(station.id, e.currentTarget.checked)}
               class="sr-only peer">
        <div class="w-[72px] h-10 bg-gray-300 border border-gray-300 rounded-full peer dark:bg-gray-600 dark:border-gray-600 peer-checked:after:translate-x-8 peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:border-gray-300 after:rounded-full after:h-9 after:w-9 after:transition-all peer-checked:bg-green-600 peer-checked:border-green-600"></div>
      </label>
    </div>
  </div>
</div>

<style>
  /* Component-specific styles can go here */
</style> 