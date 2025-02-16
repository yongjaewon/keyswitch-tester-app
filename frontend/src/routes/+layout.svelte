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

<div class="min-h-screen bg-gray-200 dark:bg-gray-900 flex flex-col">
  <div class="fixed top-0 left-0 right-0 z-10 bg-gray-200 dark:bg-gray-900">
    <Navbar />
  </div>
  <main class="flex-1 pt-20 flex">
    <slot />
  </main>
</div>

<!-- Connection-related modals at the highest level -->
<LoadingScreen />

<style global>
  /* Disable zooming and unwanted touch behaviors globally */
  html, body {
    touch-action: pan-x pan-y;
    -webkit-touch-callout: none;
    -webkit-user-select: none;
    user-select: none;
    overscroll-behavior: none;
  }

  * {
    touch-action: manipulation;
    -webkit-tap-highlight-color: transparent;
  }
</style> 