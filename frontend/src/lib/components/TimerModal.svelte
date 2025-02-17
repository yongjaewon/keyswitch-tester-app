<script lang="ts">
  import { appStore, actions } from '../stores/appStore';
  import type { AppState } from '../stores/appStore';
  import { TIMER_SETTINGS } from '../constants';
  import { onMount } from 'svelte';
  import NumPad from './NumPad.svelte';

  let editing_hours = 0;
  let editing_minutes = 0;
  let show_numpad = false;
  let current_field: {
    key: 'hours' | 'minutes';
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
    const state = $appStore;
    if (state.timer_end_time) {
      const end_time = new Date(state.timer_end_time);
      const now = new Date();
      const diff_ms = end_time.getTime() - now.getTime();
      const diff_hours = Math.floor(diff_ms / (1000 * 60 * 60));
      const diff_minutes = Math.floor((diff_ms % (1000 * 60 * 60)) / (1000 * 60));
      editing_hours = diff_hours;
      editing_minutes = diff_minutes;
    } else {
      editing_hours = 0;
      editing_minutes = 0;
    }

    // Add event listener for Escape key
    window.addEventListener('keydown', handleEscape);

    // Cleanup function
    return () => {
      window.removeEventListener('keydown', handleEscape);
    };
  });

  function closeModal() {
    appStore.update((state: AppState) => ({ ...state, show_timer_modal: false }));
  }

  async function saveTimer() {
    await actions.setTimer(editing_hours, editing_minutes);
  }

  function handleInputClick(key: 'hours' | 'minutes') {
    const config = key === 'hours' 
      ? { min: 0, max: TIMER_SETTINGS.MAX_HOURS, step: 1, unit: 'hrs' }
      : { min: 0, max: 59, step: 1, unit: 'min' };
    
    current_field = { 
      key, 
      label: key === 'hours' ? 'Hours' : 'Minutes',
      ...config
    };
    show_numpad = true;
  }

  function handleNumpadSubmit(event: CustomEvent<{ value: number }>) {
    if (current_field) {
      if (current_field.key === 'hours') {
        editing_hours = event.detail.value;
      } else {
        editing_minutes = event.detail.value;
      }
    }
    show_numpad = false;
    current_field = null;
  }

  function handleNumpadCancel() {
    show_numpad = false;
    current_field = null;
  }

  function incrementHours() {
    editing_hours = (editing_hours + 1) % (TIMER_SETTINGS.MAX_HOURS + 1);
  }

  function decrementHours() {
    editing_hours = editing_hours > 0 ? editing_hours - 1 : TIMER_SETTINGS.MAX_HOURS;
  }

  function incrementMinutes() {
    editing_minutes = (editing_minutes + 1) % 60;
  }

  function decrementMinutes() {
    editing_minutes = editing_minutes > 0 ? editing_minutes - 1 : 59;
  }
</script>

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
  <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-lg shadow-xl">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Set Timer</h2>
      <button 
        on:click={closeModal} 
        class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        aria-label="Close timer modal"
      >
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <div class="flex flex-col gap-4">
      <!-- Timer controls -->
      <div class="flex items-center justify-center gap-6 p-4">
        <!-- Hours -->
        <div class="flex flex-col items-center">
          <button 
            on:click={incrementHours} 
            class="p-4 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white touch-manipulation"
            aria-label="Increase hours"
            style="touch-action: manipulation;"
          >
            <svg class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
            </svg>
          </button>
          <div class="w-24 h-20 flex items-center justify-center bg-gray-100 dark:bg-gray-700 rounded-lg">
            <input
              type="number"
              inputmode="numeric"
              pattern="[0-9]*"
              bind:value={editing_hours}
              readonly
              on:click={() => handleInputClick('hours')}
              min="0"
              max={TIMER_SETTINGS.MAX_HOURS}
              class="w-full text-4xl font-bold text-gray-900 dark:text-white bg-transparent text-center focus:outline-none touch-manipulation cursor-pointer"
              style="touch-action: manipulation; -moz-appearance: textfield;"
            >
          </div>
          <button 
            on:click={decrementHours}
            class="p-4 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white touch-manipulation"
            aria-label="Decrease hours"
            style="touch-action: manipulation;"
          >
            <svg class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <span class="text-xl text-gray-600 dark:text-gray-400 mt-2 font-medium">Hours</span>
        </div>

        <div class="h-20 flex items-center -mt-10">
          <span class="text-4xl font-bold text-gray-900 dark:text-white">:</span>
        </div>

        <!-- Minutes -->
        <div class="flex flex-col items-center">
          <button 
            on:click={incrementMinutes}
            class="p-4 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white touch-manipulation"
            aria-label="Increase minutes"
            style="touch-action: manipulation;"
          >
            <svg class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
            </svg>
          </button>
          <div class="w-24 h-20 flex items-center justify-center bg-gray-100 dark:bg-gray-700 rounded-lg">
            <input
              type="number"
              inputmode="numeric"
              pattern="[0-9]*"
              bind:value={editing_minutes}
              readonly
              on:click={() => handleInputClick('minutes')}
              min="0"
              max="59"
              class="w-full text-4xl font-bold text-gray-900 dark:text-white bg-transparent text-center focus:outline-none touch-manipulation cursor-pointer"
              style="touch-action: manipulation; -moz-appearance: textfield;"
            >
          </div>
          <button 
            on:click={decrementMinutes}
            class="p-4 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white touch-manipulation"
            aria-label="Decrease minutes"
            style="touch-action: manipulation;"
          >
            <svg class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <span class="text-xl text-gray-600 dark:text-gray-400 mt-2 font-medium">Minutes</span>
        </div>
      </div>

      <div class="flex justify-end gap-4 mt-6">
        <button on:click={closeModal} 
                class="px-8 py-4 text-2xl text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200">
          Cancel
        </button>
        <button on:click={saveTimer}
                class="px-8 py-4 text-2xl bg-green-600 text-white rounded-lg hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800">
          Set Timer
        </button>
      </div>
    </div>
  </div>
</div>

{#if show_numpad && current_field}
  <div class="z-[70]">
    <NumPad
      value={current_field.key === 'hours' ? editing_hours.toString() : editing_minutes.toString()}
      min={current_field.min}
      max={current_field.max}
      step={current_field.step}
      allowDecimal={false}
      label={current_field.label}
      unit={current_field.unit}
      on:submit={handleNumpadSubmit}
      on:cancel={handleNumpadCancel}
    />
  </div>
{/if}

<style>
  /* Remove focus outlines globally */
  :global(*:focus) {
    outline: none !important;
  }

  /* Disable double-tap zoom on mobile */
  :global(.touch-manipulation) {
    touch-action: manipulation;
  }

  /* Prevent text selection */
  :global(.touch-manipulation) {
    user-select: none;
    -webkit-user-select: none;
  }

  /* Hide number input spinners for all browsers */
  :global(input[type="number"]::-webkit-outer-spin-button),
  :global(input[type="number"]::-webkit-inner-spin-button) {
    -webkit-appearance: none;
    margin: 0;
  }

  /* Firefox */
  :global(input[type="number"]) {
    appearance: textfield;
    -moz-appearance: textfield;
  }
</style> 
