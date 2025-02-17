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

  function handleCheckboxChange(stationId: number, e: Event): void {
    const target = e.currentTarget as HTMLInputElement;
    actions.setStationState(stationId, target.checked);
  }
</script>

<div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-300/90 dark:border-gray-700 shadow-md lg:h-[114px] lg:flex-none">
  <div class="p-[14px] h-full flex">
    <!-- Main content area (clickable) -->
    <div class="flex-1">
      <!-- Mobile layout (2x2 grid) for screens below 640px -->
      <div class="min-[620px]:hidden">
        <!-- Top row: Station ID and toggle switch -->
        <div class="grid grid-cols-2 gap-4 mb-[14px]">
          <!-- Top Left: Station ID -->
          <div class="flex items-center">
            <h3 class="text-xl min-[450px]:text-2xl font-bold text-gray-900 dark:text-white whitespace-nowrap">Station {station.id}</h3>
            <button 
              class="ml-2 p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              aria-label="Edit station settings"
              on:click={() => {
                appStore.update((s: any) => ({ 
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
          <div class="flex justify-end items-center pt-0.5">
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" 
                     checked={station.enabled}
                     on:change={(e: Event) => handleCheckboxChange(station.id, e)}
                     class="sr-only peer">
              <div class="w-[72px] h-10 bg-gray-300 border border-gray-300 rounded-full peer dark:bg-gray-600 dark:border-gray-600 peer-checked:after:translate-x-8 peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:border-gray-300 after:rounded-full after:h-9 after:w-9 after:transition-all peer-checked:bg-green-600 peer-checked:border-green-600"></div>
            </label>
          </div>
        </div>

        <!-- Status boxes container -->
        <div class="flex flex-col min-[410px]:flex-row gap-4">
          <!-- Cycle count -->
          <div class="relative flex flex-col py-1 bg-gray-100 dark:bg-gray-700/50 rounded-lg min-h-[60px] min-[410px]:min-w-[80px] min-[410px]:flex-1">
            <div class="absolute inset-0 flex items-center justify-center min-[410px]:-mt-[5px]">
              <div class="flex items-baseline gap-2">
                <div class="text-2xl min-[450px]:text-3xl font-bold text-gray-900 dark:text-white">
                  {station.current_cycles.toLocaleString()}
                </div>
                <div class="text-base font-medium text-gray-500 dark:text-gray-400 min-[410px]:hidden">
                  Cycles
                </div>
              </div>
            </div>
            <div class="absolute bottom-4 left-0 right-0 text-base font-medium text-center text-gray-500 dark:text-gray-400 hidden min-[410px]:block min-[410px]:-mt-[5px]">
              Cycles
            </div>
          </div>

          <!-- Status cards -->
          <div class="grid grid-cols-2 gap-4">
            <!-- Bottom Left: Motor Status -->
            <div class="flex flex-col gap-1 p-3 bg-gray-100 dark:bg-gray-700/50 rounded-lg w-full min-[410px]:w-[97px]">
              <div class="flex items-center justify-center relative">
                <span class="text-base font-semibold text-gray-700 dark:text-gray-300">Motor</span>
                <div class="absolute right-0 w-2 h-2 rounded-full {motor_indicator_state}"></div>
              </div>
              <div class="flex justify-center">
                <div class="text-base font-bold px-2 py-[1px] rounded-full {getCurrentBadgeClass(station.motor_current, motor_current_threshold)}">
                  {station.motor_current}
                </div>
              </div>
              <div class="flex justify-center">
                <div class="text-base font-bold px-2 py-[1px] rounded-full {getFailureBadgeClass(station.motor_failures, motor_failure_threshold)}">
                  {station.motor_failures} Fails
                </div>
              </div>
            </div>

            <!-- Bottom Right: Switch Status -->
            <div class="flex flex-col gap-1 p-3 bg-gray-100 dark:bg-gray-700/50 rounded-lg w-full min-[410px]:w-[97px]">
              <div class="flex items-center justify-center relative">
                <span class="text-base font-semibold text-gray-700 dark:text-gray-300">Switch</span>
                <div class="absolute right-0 w-2 h-2 rounded-full {switch_indicator_state}"></div>
              </div>
              <div class="flex justify-center">
                <div class="text-base font-bold px-2 py-[1px] rounded-full {getCurrentBadgeClass(station.switch_current, switch_current_threshold)}">
                  {station.switch_current}
                </div>
              </div>
              <div class="flex justify-center">
                <div class="text-base font-bold px-2 py-[1px] rounded-full {getFailureBadgeClass(station.switch_failures, switch_failure_threshold)}">
                  {station.switch_failures} Fails
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tablet/Desktop layout (horizontal layout) -->
      <div class="hidden min-[620px]:flex items-center h-full">
        <!-- Station info -->
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <h3 class="text-2xl font-bold text-gray-900 dark:text-white">Station {station.id}</h3>
            <button 
              class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              aria-label="Edit station settings"
              on:click={() => {
                appStore.update((s: any) => ({ 
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
              <div class="flex justify-center">
                <div class="text-base font-bold px-2 py-0.5 rounded-full {getCurrentBadgeClass(station.motor_current, motor_current_threshold)}">
                  {station.motor_current}
                </div>
              </div>
              <div class="flex justify-center mt-0 min-[620px]:mt-1">
                <div class="text-base font-bold px-2 py-0.5 rounded-full {getFailureBadgeClass(station.motor_failures, motor_failure_threshold)}">
                  {station.motor_failures} Fails
                </div>
              </div>
            </div>
          </div>

          <div class="h-16 w-px bg-gray-400 dark:bg-gray-500"></div>

          <div class="flex-1 flex flex-col items-center px-2">
            <div class="relative flex items-center h-6">
              <span class="text-base font-semibold text-gray-700 dark:text-gray-300">Switch</span>
              <div class="absolute -right-3 w-2 h-2 rounded-full {switch_indicator_state}"></div>
            </div>
            <div class="flex flex-col items-center w-[120px]">
              <div class="flex justify-center">
                <div class="text-base font-bold px-2 py-0.5 rounded-full {getCurrentBadgeClass(station.switch_current, switch_current_threshold)}">
                  {station.switch_current}
                </div>
              </div>
              <div class="flex justify-center mt-0 min-[620px]:mt-1">
                <div class="text-base font-bold px-2 py-0.5 rounded-full {getFailureBadgeClass(station.switch_failures, switch_failure_threshold)}">
                  {station.switch_failures} Fails
                </div>
              </div>
            </div>
          </div>

          <div class="h-16 w-px bg-gray-400 dark:bg-gray-500"></div>
        </div>
      </div>
    </div>

    <!-- Toggle switch area (tablet/desktop only) -->
    <div class="hidden min-[620px]:flex items-center min-[620px]:ml-5 min-[620px]:mr-2">
      <label class="relative inline-flex items-center cursor-pointer">
        <input type="checkbox" 
               checked={station.enabled}
               on:change={(e: Event) => handleCheckboxChange(station.id, e)}
               class="sr-only peer">
        <div class="w-[72px] h-10 bg-gray-300 border border-gray-300 rounded-full peer dark:bg-gray-600 dark:border-gray-600 peer-checked:after:translate-x-8 peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:border-gray-300 after:rounded-full after:h-9 after:w-9 after:transition-all peer-checked:bg-green-600 peer-checked:border-green-600"></div>
      </label>
    </div>
  </div>
</div>

<style>
  /* Component-specific styles can go here */
</style> 