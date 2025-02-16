<script lang="ts">
    import { connectionStore } from '../stores/connectionStore';
    import type { ConnectionState } from '../stores/connectionStore';
    import { fade } from 'svelte/transition';

    $: state = $connectionStore;
    $: show_loading = state.is_initializing || state.is_first_connection || !state.is_data_loaded;
    $: message = getLoadingMessage(state);

    function getLoadingMessage(state: ConnectionState): string {
        if (!state.is_connected && state.has_reached_max_attempts) {
            return 'Connection failed';
        }
        if (!state.is_connected) {
            return 'Connecting to server...';
        }
        if (!state.is_data_loaded) {
            return 'Connecting to server...';
        }
        return 'Starting application...';
    }

    function handleRetry() {
        connectionStore.retry();
    }
</script>

{#if show_loading}
    <div class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 flex items-center justify-center">
        <div class="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-xl flex flex-col items-center">
            <div class="animate-spin rounded-full h-12 w-12 border-4 border-gray-300 dark:border-gray-600 border-t-blue-600"></div>
            <p class="mt-4 text-lg font-medium text-gray-900 dark:text-white">{message}</p>
            {#if state.has_reached_max_attempts}
                <button
                    on:click={handleRetry}
                    class="mt-6 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
                >
                    Try Again
                </button>
            {/if}
        </div>
    </div>
{/if} 