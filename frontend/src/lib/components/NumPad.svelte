<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let value: string = '0';
  export let min: number = 0;
  export let max: number = 999999;
  export let step: number = 1;
  export let allowDecimal: boolean = true;
  export let label: string = '';
  export let unit: string = '';

  const dispatch = createEventDispatcher();

  function handleNumber(num: number) {
    if (value === '0') {
      value = num.toString();
    } else {
      if (value.length < 10) {  // Allow up to 10 digits
        value += num;
      }
    }
  }

  function handleDecimal() {
    if (!allowDecimal || value.includes('.')) return;
    value += '.';
  }

  function handleBackspace() {
    if (value.length <= 1) {
      value = '0';
    } else {
      value = value.slice(0, -1);
    }
  }

  function validateValue() {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
      value = '0';
      return false;
    }

    // Round to the number of decimal places in the step
    const decimalPlaces = step.toString().split('.')[1]?.length || 0;
    const roundedValue = Number(numValue.toFixed(decimalPlaces));

    // Check if value is within bounds
    if (roundedValue > max || roundedValue < min) {
      return false;
    }

    value = roundedValue.toString();
    return true;
  }

  function handleSubmit() {
    if (validateValue()) {
      dispatch('submit', { value: parseFloat(value) });
    } else {
      // Show validation error message
      alert(`Please enter a value between ${min} and ${max}`);
    }
  }

  function handleCancel() {
    dispatch('cancel');
  }
</script>

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-sm">
    <!-- Header -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
      <div class="flex justify-between items-center">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{label}</h3>
        <button 
          on:click={handleCancel}
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        >
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div class="mt-2 bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
        <div class="text-right text-3xl font-mono text-gray-900 dark:text-white">
          {value}{#if unit} <span class="text-xl text-gray-600 dark:text-gray-400">{unit}</span>{/if}
        </div>
      </div>
    </div>

    <!-- Numpad Grid -->
    <div class="p-4">
      <div class="grid grid-cols-3 gap-2">
        {#each [7, 8, 9, 4, 5, 6, 1, 2, 3] as num}
          <button
            on:click={() => handleNumber(num)}
            class="p-4 text-2xl font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition-colors"
          >
            {num}
          </button>
        {/each}
        
        <!-- Bottom row -->
        <button
          on:click={() => handleDecimal()}
          disabled={!allowDecimal}
          class="p-4 text-2xl font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          .
        </button>
        <button
          on:click={() => handleNumber(0)}
          class="p-4 text-2xl font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition-colors"
        >
          0
        </button>
        <button
          on:click={handleBackspace}
          class="p-4 text-xl font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition-colors"
        >
          ←
        </button>
      </div>

      <!-- Action buttons -->
      <div class="grid grid-cols-2 gap-2 mt-2">
        <button
          on:click={handleCancel}
          class="p-4 text-xl font-semibold text-gray-600 dark:text-gray-400 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition-colors"
        >
          Cancel
        </button>
        <button
          on:click={handleSubmit}
          class="p-4 text-xl font-semibold text-white bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800 rounded-lg transition-colors"
        >
          Enter
        </button>
      </div>
    </div>
  </div>
</div> 