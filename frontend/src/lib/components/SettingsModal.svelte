<script lang="ts">
  import { appStore, actions } from '../stores/appStore';
  import type { AppState } from '../stores/appStore';
  import { onMount } from 'svelte';
  import { isLocalBackend } from '../utils';
  import NumPad from './NumPad.svelte';

  let editing_settings: Partial<AppState> = {};
  let show_numpad = false;
  let current_field: {
    key: keyof Partial<AppState>;
    label: string;
    min: number;
    max: number;
    step: number;
    unit: string;
  } | null = null;

  function handleEscape(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      closeModal();
    }
  }

  // Initialize values when modal opens
  onMount(() => {
    // Get initial values from store
    const state = $appStore;
    editing_settings = {
      cutoff_voltage: state.cutoff_voltage,
      motor_current_threshold: state.motor_current_threshold,
      switch_current_threshold: state.switch_current_threshold,
      cycle_limit: state.cycle_limit,
      motor_failure_threshold: state.motor_failure_threshold,
      switch_failure_threshold: state.switch_failure_threshold,
      cycles_per_minute: state.cycles_per_minute
    };

    // Add event listener for Escape key
    window.addEventListener('keydown', handleEscape);

    // Cleanup function
    return () => {
      window.removeEventListener('keydown', handleEscape);
    };
  });

  function closeModal() {
    appStore.update((state: AppState) => ({ ...state, show_settings_modal: false }));
  }

  function handleInputClick(key: keyof Partial<AppState>, config: { label: string, min: number, max: number, step: number, unit: string }) {
    if (isLocalBackend()) {
      current_field = { key, ...config };
      show_numpad = true;
    }
  }

  function handleNumpadSubmit(event: CustomEvent<{ value: number }>) {
    if (current_field) {
      editing_settings[current_field.key] = event.detail.value as any;
    }
    show_numpad = false;
    current_field = null;
  }

  function handleNumpadCancel() {
    show_numpad = false;
    current_field = null;
  }

  async function saveSettings() {
    // Validate values before saving
    const validationErrors = [];
    
    // Validate cutoff voltage (10.5-13.5V)
    if (editing_settings.cutoff_voltage === undefined || 
        editing_settings.cutoff_voltage < 10.5 || 
        editing_settings.cutoff_voltage > 13.5) {
      validationErrors.push("Cutoff voltage must be between 10.5V and 13.5V");
    }
    
    // Validate motor current threshold (50-200A)
    if (editing_settings.motor_current_threshold === undefined || 
        editing_settings.motor_current_threshold < 50.0 || 
        editing_settings.motor_current_threshold > 200.0) {
      validationErrors.push("Motor current threshold must be between 50A and 200A");
    }
    
    // Validate switch current threshold (0.1-50A)
    if (editing_settings.switch_current_threshold === undefined || 
        editing_settings.switch_current_threshold < 0.1 || 
        editing_settings.switch_current_threshold > 50.0) {
      validationErrors.push("Switch current threshold must be between 0.1A and 50A");
    }
    
    // Validate cycle limit (1-1,000,000)
    if (editing_settings.cycle_limit === undefined || 
        editing_settings.cycle_limit < 1 || 
        editing_settings.cycle_limit > 1000000) {
      validationErrors.push("Cycle limit must be between 1 and 1,000,000");
    }
    
    // Validate motor failure threshold (1-1,000)
    if (editing_settings.motor_failure_threshold === undefined || 
        editing_settings.motor_failure_threshold < 1 || 
        editing_settings.motor_failure_threshold > 1000) {
      validationErrors.push("Motor failure threshold must be between 1 and 1,000");
    }
    
    // Validate switch failure threshold (1-1,000)
    if (editing_settings.switch_failure_threshold === undefined || 
        editing_settings.switch_failure_threshold < 1 || 
        editing_settings.switch_failure_threshold > 1000) {
      validationErrors.push("Switch failure threshold must be between 1 and 1,000");
    }
    
    // Validate cycles per minute (1-12)
    if (editing_settings.cycles_per_minute === undefined || 
        editing_settings.cycles_per_minute < 1 || 
        editing_settings.cycles_per_minute > 12) {
      validationErrors.push("Cycles per minute must be between 1 and 12");
    }

    // Round numeric values to appropriate decimal places
    if (editing_settings.cutoff_voltage !== undefined) {
      editing_settings.cutoff_voltage = Number(editing_settings.cutoff_voltage.toFixed(1));
    }
    if (editing_settings.motor_current_threshold !== undefined) {
      editing_settings.motor_current_threshold = Number(editing_settings.motor_current_threshold.toFixed(1));
    }
    if (editing_settings.switch_current_threshold !== undefined) {
      editing_settings.switch_current_threshold = Number(editing_settings.switch_current_threshold.toFixed(1));
    }

    // If there are validation errors, show them and don't save
    if (validationErrors.length > 0) {
      alert(validationErrors.join("\n"));
      return;
    }

    await actions.saveSettings(editing_settings);
    closeModal();
  }
</script>

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-start sm:items-center justify-center z-[60] p-3">
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
    <!-- Header -->
    <div class="flex justify-between items-center p-3 sm:p-4 border-b border-gray-200 dark:border-gray-700">
      <h2 class="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">System Settings</h2>
      <button on:click={closeModal} class="p-1.5 sm:p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
        <svg class="w-5 h-5 sm:w-6 sm:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <!-- Content with scroll -->
    <div class="flex-1 overflow-y-auto min-h-0 p-2 sm:p-3">
      <!-- Settings form -->
      <div class="grid grid-cols-1 min-[800px]:grid-cols-2 min-[1200px]:grid-cols-4 gap-2 sm:gap-3">
        <!-- Voltage Settings Group -->
        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2 sm:p-3 min-w-[250px]">
          <h3 class="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-2">Voltage Settings</h3>
          <div class="flex flex-col gap-2 sm:gap-3">
            <!-- Cutoff Voltage -->
            <div class="flex flex-col gap-1">
              <label class="text-sm sm:text-base font-medium text-gray-700 dark:text-gray-300">
                Cutoff Voltage (V)
              </label>
              <input
                type="number"
                inputmode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                bind:value={editing_settings.cutoff_voltage}
                min="10.5"
                max="13.5"
                step="0.1"
                on:click={() => handleInputClick('cutoff_voltage', {
                  label: 'Cutoff Voltage',
                  min: 10.5,
                  max: 13.5,
                  step: 0.1,
                  unit: 'V'
                })}
                class="px-2 py-1.5 sm:px-3 sm:py-2 text-base sm:text-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
          </div>
        </div>

        <!-- Cycle Settings Group -->
        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2 sm:p-3 min-w-[250px]">
          <h3 class="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-2">Cycle Settings</h3>
          <div class="flex flex-col gap-2 sm:gap-3">
            <!-- Cycles Per Minute -->
            <div class="flex flex-col gap-1">
              <label class="text-sm sm:text-base font-medium text-gray-700 dark:text-gray-300">
                Rate (cycles/min)
              </label>
              <input
                type="number"
                inputmode="numeric"
                pattern="[0-9]*"
                bind:value={editing_settings.cycles_per_minute}
                min="1"
                max="12"
                step="1"
                on:click={() => handleInputClick('cycles_per_minute', {
                  label: 'Cycles Per Minute',
                  min: 1,
                  max: 12,
                  step: 1,
                  unit: 'cyc/min'
                })}
                class="px-2 py-1.5 sm:px-3 sm:py-2 text-base sm:text-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>

            <!-- Cycle Limit -->
            <div class="flex flex-col gap-1">
              <label class="text-sm sm:text-base font-medium text-gray-700 dark:text-gray-300">
                Cycle Limit
              </label>
              <input
                type="number"
                inputmode="numeric"
                pattern="[0-9]*"
                bind:value={editing_settings.cycle_limit}
                min="1"
                max="1000000"
                step="1000"
                on:click={() => handleInputClick('cycle_limit', {
                  label: 'Cycle Limit',
                  min: 1,
                  max: 1000000,
                  step: 1000,
                  unit: ''
                })}
                class="px-2 py-1.5 sm:px-3 sm:py-2 text-base sm:text-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
          </div>
        </div>

        <!-- Motor Settings Group -->
        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2 sm:p-3 min-w-[250px]">
          <h3 class="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-2">Motor Settings</h3>
          <div class="flex flex-col gap-2 sm:gap-3">
            <!-- Motor Current Threshold -->
            <div class="flex flex-col gap-1">
              <label class="text-sm sm:text-base font-medium text-gray-700 dark:text-gray-300">
                Current Threshold (A)
              </label>
              <input
                type="number"
                inputmode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                bind:value={editing_settings.motor_current_threshold}
                min="50.0"
                max="200.0"
                step="0.1"
                on:click={() => handleInputClick('motor_current_threshold', {
                  label: 'Motor Current Threshold',
                  min: 50.0,
                  max: 200.0,
                  step: 0.1,
                  unit: 'A'
                })}
                class="px-2 py-1.5 sm:px-3 sm:py-2 text-base sm:text-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>

            <!-- Motor Failure Threshold -->
            <div class="flex flex-col gap-1">
              <label class="text-sm sm:text-base font-medium text-gray-700 dark:text-gray-300">
                Failure Threshold
              </label>
              <input
                type="number"
                inputmode="numeric"
                pattern="[0-9]*"
                bind:value={editing_settings.motor_failure_threshold}
                min="1"
                max="1000"
                step="1"
                on:click={() => handleInputClick('motor_failure_threshold', {
                  label: 'Motor Failure Threshold',
                  min: 1,
                  max: 1000,
                  step: 1,
                  unit: ''
                })}
                class="px-2 py-1.5 sm:px-3 sm:py-2 text-base sm:text-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
          </div>
        </div>

        <!-- Switch Settings Group -->
        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2 sm:p-3 min-w-[250px]">
          <h3 class="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-2">Switch Settings</h3>
          <div class="flex flex-col gap-2 sm:gap-3">
            <!-- Switch Current Threshold -->
            <div class="flex flex-col gap-1">
              <label class="text-sm sm:text-base font-medium text-gray-700 dark:text-gray-300">
                Current Threshold (A)
              </label>
              <input
                type="number"
                inputmode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                bind:value={editing_settings.switch_current_threshold}
                min="0.1"
                max="50.0"
                step="0.1"
                on:click={() => handleInputClick('switch_current_threshold', {
                  label: 'Switch Current Threshold',
                  min: 0.1,
                  max: 50.0,
                  step: 0.1,
                  unit: 'A'
                })}
                class="px-2 py-1.5 sm:px-3 sm:py-2 text-base sm:text-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>

            <!-- Switch Failure Threshold -->
            <div class="flex flex-col gap-1">
              <label class="text-sm sm:text-base font-medium text-gray-700 dark:text-gray-300">
                Failure Threshold
              </label>
              <input
                type="number"
                inputmode="numeric"
                pattern="[0-9]*"
                bind:value={editing_settings.switch_failure_threshold}
                min="1"
                max="1000"
                step="1"
                on:click={() => handleInputClick('switch_failure_threshold', {
                  label: 'Switch Failure Threshold',
                  min: 1,
                  max: 1000,
                  step: 1,
                  unit: ''
                })}
                class="px-2 py-1.5 sm:px-3 sm:py-2 text-base sm:text-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="border-t border-gray-200 dark:border-gray-700 p-2 sm:p-3">
      <div class="flex flex-col-reverse sm:flex-row justify-end gap-2 sm:gap-3">
        <button on:click={closeModal} 
                class="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 text-base sm:text-lg text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 bg-gray-100 dark:bg-gray-700 rounded-lg">
          Cancel
        </button>
        <button on:click={saveSettings}
                class="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 text-base sm:text-lg bg-green-600 text-white rounded-lg hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800">
          Save Settings
        </button>
      </div>
    </div>
  </div>
</div>

{#if show_numpad && current_field}
  <div class="z-[70]">
    <NumPad
      value={editing_settings[current_field.key]?.toString() || '0'}
      min={current_field.min}
      max={current_field.max}
      step={current_field.step}
      allowDecimal={current_field.step < 1}
      label={current_field.label}
      unit={current_field.unit}
      on:submit={handleNumpadSubmit}
      on:cancel={handleNumpadCancel}
    />
  </div>
{/if} 