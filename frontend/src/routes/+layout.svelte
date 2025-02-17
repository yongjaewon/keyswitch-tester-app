<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import { initializeWebSocket } from '$lib/services/api';
  import LoadingScreen from '$lib/components/LoadingScreen.svelte';
  import Navbar from '$lib/components/Navbar.svelte';
  import { connectionStore } from '$lib/stores/connectionStore';

  onMount(() => {
    initializeWebSocket();
    return () => {
      connectionStore.reset();
    };
  });
</script>

<div class="fixed inset-0 bg-gray-200 dark:bg-gray-900"></div>
<div class="relative min-h-screen flex flex-col">
  <div class="fixed top-0 left-0 right-0 z-10">
    <Navbar />
  </div>
  <main class="flex-1 pt-20 flex">
    <slot />
  </main>
</div>

<!-- Connection-related modals at the highest level -->
<LoadingScreen />