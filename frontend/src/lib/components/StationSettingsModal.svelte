<script lang="ts">
  import { appStore, actions } from '../stores/appStore';
  import type { AppState, Station } from '../stores/appStore';
  import { onMount } from 'svelte';
  import NumPad from './NumPad.svelte';

  export let station: Station;
  
  let show_numpad = false;
  let current_field: {
    key: keyof typeof editing_values;
    label: string;
  } | null = null;
  
  let editing_values = {
    current_cycles: station.current_cycles,
    motor_failures: station.motor_failures,
    switch_failures: station.switch_failures
  };

  function handleEscape(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      closeModal();
    }
  }

  onMount(() => {
    // Add event listener for Escape key
    window.addEventListener('keydown', handleEscape);

    // Cleanup function
    return () => {
      window.removeEventListener('keydown', handleEscape);
    };
  });

  function closeModal() {
    appStore.update((state: AppState) => ({ 
      ...state, 
      show_station_settings_modal: false,
      selected_station: null
    }));
  }

  function handleReset() {
    editing_values = {
      current_cycles: 0,
      motor_failures: 0,
      switch_failures: 0
    };
  }

  async function handleSave() {
    try {
      await actions.updateStationSettings(station.id, editing_values);
    } catch (error) {
      console.error('Failed to save station settings:', error);
      // You might want to show an error message to the user here
    }
  }

  function handleNumpadSubmit(event: CustomEvent<{ value: number }>) {
    if (current_field) {
      editing_values[current_field.key] = event.detail.value;
    }
    show_numpad = false;
    current_field = null;
  }

  function handleNumpadCancel() {
    show_numpad = false;
    current_field = null;
  }

  function handleInputClick(key: keyof typeof editing_values, label: string) {
    current_field = { key, label };
    show_numpad = true;
  }
</script>

{#if show_numpad && current_field}
  <div class="z-[70]">
    <NumPad
      value={editing_values[current_field.key]?.toString() || '0'}
      min={0}
      max={999999}
      step={1}
      allowDecimal={false}
      label={current_field.label}
      unit=""
      on:submit={handleNumpadSubmit}
      on:cancel={handleNumpadCancel}
    />
  </div>
{/if}

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
  <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 shadow-xl">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Station {station.id} Settings</h2>
      <button 
        on:click={closeModal} 
        aria-label="Close station settings"
        class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
      >
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <div class="flex flex-col gap-6">
      <!-- Current Cycles -->
      <div class="flex flex-col gap-2">
        <label for="currentCycles" class="text-sm font-medium text-gray-700 dark:text-gray-300">
          Current Cycles
        </label>
        <input
          id="currentCycles"
          type="number"
          bind:value={editing_values.current_cycles}
          min="0"
          readonly
          on:click={() => handleInputClick('current_cycles', 'Current Cycles')}
          class="px-3 py-2 text-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white cursor-pointer"
        />
      </div>

      <!-- Motor Failures -->
      <div class="flex flex-col gap-2">
        <label for="motorFailures" class="text-sm font-medium text-gray-700 dark:text-gray-300">
          Motor Failures
        </label>
        <input
          id="motorFailures"
          type="number"
          bind:value={editing_values.motor_failures}
          min="0"
          readonly
          on:click={() => handleInputClick('motor_failures', 'Motor Failures')}
          class="px-3 py-2 text-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white cursor-pointer"
        />
      </div>

      <!-- Switch Failures -->
      <div class="flex flex-col gap-2">
        <label for="switchFailures" class="text-sm font-medium text-gray-700 dark:text-gray-300">
          Switch Failures
        </label>
        <input
          id="switchFailures"
          type="number"
          bind:value={editing_values.switch_failures}
          min="0"
          readonly
          on:click={() => handleInputClick('switch_failures', 'Switch Failures')}
          class="px-3 py-2 text-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white cursor-pointer"
        />
      </div>

      <div class="flex justify-between gap-4 mt-2">
        <button 
          on:click={handleReset}
          class="px-4 py-2 text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
        >
          Reset All
        </button>
        <div class="flex gap-4">
          <button 
            on:click={closeModal}
            class="px-4 py-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
          >
            Cancel
          </button>
          <button
            on:click={handleSave}
            class="px-4 py-2 text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  /* Ensure inputs don't show spinners */
  input[type="number"]::-webkit-outer-spin-button,
  input[type="number"]::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }

  input[type="number"] {
    -moz-appearance: textfield;
    appearance: textfield;
  }
</style> 