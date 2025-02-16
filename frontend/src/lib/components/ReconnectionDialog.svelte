<script lang="ts">
    import { connectionStore } from '../stores/connectionStore';
    import { fade } from 'svelte/transition';

    $: state = $connectionStore;
    $: show_dialog = !state.is_initializing && !state.is_connected && !state.is_first_connection;

    function handleManualReconnect() {
        connectionStore.retry();
    }
</script>

{#if show_dialog}
    <div class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 flex items-center justify-center" transition:fade>
        <div class="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full mx-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">Connection Lost</h2>
            <p class="text-gray-600 dark:text-gray-300 mb-6">
                {#if state.has_reached_max_attempts}
                    Lost connection to the server.
                {:else if state.reconnect_attempt > 0}
                    Attempting to reconnect... (Attempt {state.reconnect_attempt})
                {:else}
                    Lost connection to the server. The application will automatically attempt to reconnect.
                {/if}
            </p>
            <div class="flex justify-end gap-4">
                {#if state.reconnect_attempt > 0 && !state.has_reached_max_attempts}
                    <div class="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500"></div>
                {:else}
                    <button
                        class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                        on:click={handleManualReconnect}
                    >
                        Reconnect Now
                    </button>
                {/if}
            </div>
        </div>
    </div>
{/if} 