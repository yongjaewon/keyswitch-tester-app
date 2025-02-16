<script lang="ts">
  import { appStore, actions } from '../stores/appStore';
  import type { AppState } from '../stores/appStore';
  import orangeLogo from '$lib/assets/logos/WRIGHT_LOGO_ORANGE.svg?url';
  import { onMount } from 'svelte';
  
  let isMenuOpen = false;
  let isDarkMode = false;
  let themeMode: 'light' | 'dark' | 'auto' = 'auto';
  
  // Subscribe to store
  let state: AppState;
  appStore.subscribe((newState: AppState) => {
    state = newState;
  });
  
  function updateTheme(mode: typeof themeMode) {
    const isSystemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    isDarkMode = mode === 'auto' ? isSystemDark : mode === 'dark';
    document.documentElement.classList.toggle('dark', isDarkMode);
  }

  function handleSystemThemeChange(e: MediaQueryListEvent) {
    if (themeMode === 'auto') {
      updateTheme('auto');
    }
  }
  
  onMount(() => {
    // Get stored theme preference
    const storedTheme = localStorage.getItem('theme-mode') as typeof themeMode || 'auto';
    themeMode = storedTheme;
    updateTheme(themeMode);

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', handleSystemThemeChange);

    return () => {
      mediaQuery.removeEventListener('change', handleSystemThemeChange);
    };
  });
  
  function setPage(page: AppState['current_page']) {
    appStore.update(s => ({ ...s, current_page: page }));
    isMenuOpen = false;
  }

  function cycleTheme() {
    const modes: Array<typeof themeMode> = ['light', 'dark', 'auto'];
    const currentIndex = modes.indexOf(themeMode);
    themeMode = modes[(currentIndex + 1) % modes.length];
    localStorage.setItem('theme-mode', themeMode);
    updateTheme(themeMode);
  }
</script>

<nav class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-md relative z-50">
  <div class="max-w-[1024px] mx-auto px-4">
    <div class="flex justify-between h-16">
      <!-- Logo and navigation links -->
      <div class="flex">
        <div class="flex-shrink-0 flex items-center gap-4">
          <img 
            src={orangeLogo} 
            alt="Wright Logo" 
            class="h-9 w-auto transition-transform hover:scale-105"
          />
          <span class="text-2xl font-bold text-gray-900 dark:text-white">
            <span class="min-[390px]:hidden">KST</span>
            <span class="hidden min-[390px]:inline min-[480px]:hidden">KS Tester</span>
            <span class="hidden min-[480px]:inline">KeySwitch Tester</span>
          </span>
        </div>
        <!-- Desktop navigation -->
        <div class="hidden sm:ml-8 sm:flex sm:space-x-2 sm:items-center">
          <button
            class="px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ease-in-out
                   {state.current_page === 'test' ? 
                     'bg-brand text-gray-900 shadow-lg scale-105' : 
                     'bg-gray-100 text-gray-700 hover:bg-brand hover:text-gray-900 hover:scale-105 dark:text-gray-200 dark:bg-gray-600 dark:hover:bg-brand dark:hover:text-gray-900'}"
            on:click={() => setPage('test')}
          >
            Test
          </button>
          <button
            class="px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ease-in-out
                   {state.current_page === 'data' ? 
                     'bg-brand text-gray-900 shadow-lg scale-105' : 
                     'bg-gray-100 text-gray-700 hover:bg-brand hover:text-gray-900 hover:scale-105 dark:text-gray-200 dark:bg-gray-600 dark:hover:bg-brand dark:hover:text-gray-900'}"
            on:click={() => setPage('data')}
          >
            Data
          </button>
          <button
            class="px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ease-in-out
                   {state.current_page === 'video' ? 
                     'bg-brand text-gray-900 shadow-lg scale-105' : 
                     'bg-gray-100 text-gray-700 hover:bg-brand hover:text-gray-900 hover:scale-105 dark:text-gray-200 dark:bg-gray-600 dark:hover:bg-brand dark:hover:text-gray-900'}"
            on:click={() => setPage('video')}
          >
            Camera
          </button>
        </div>
      </div>

      <!-- Theme toggle and mobile menu -->
      <div class="flex items-center gap-2">
        <!-- Theme toggle -->
        <div class="relative">
          <button
            on:click={cycleTheme}
            class="relative p-2 rounded-lg text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-700 transition-all duration-200"
            aria-label="Toggle theme"
          >
            <!-- Light mode icon -->
            <svg
              class="w-6 h-6 absolute transition-all duration-500 {themeMode === 'light' ? 'rotate-0 opacity-100 scale-100' : 'rotate-90 opacity-0 scale-75'}"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" 
              />
            </svg>
            <!-- Dark mode icon -->
            <svg
              class="w-6 h-6 absolute transition-all duration-500 {themeMode === 'dark' ? 'rotate-0 opacity-100 scale-100' : '-rotate-90 opacity-0 scale-75'}"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" 
              />
            </svg>
            <!-- Auto mode icon -->
            <svg
              class="w-6 h-6 absolute transition-all duration-500 {themeMode === 'auto' ? 'rotate-0 opacity-100 scale-100' : '-rotate-90 opacity-0 scale-75'}"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <!-- Monitor screen with rounded corners -->
              <path 
                d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6z" 
                stroke-width="2"
              />
              <!-- Sync icon inside screen -->
              <path
                d="M9 10c0-1.66 1.34-3 3-3s3 1.34 3 3-1.34 3-3 3"
                stroke-width="2"
                stroke-linecap="round"
              />
              <!-- Arrow head -->
              <path
                d="M9 10l-1-1m1 1l-1 1"
                stroke-width="2"
                stroke-linecap="round"
              />
              <!-- Stand base with curved design -->
              <path 
                d="M8 20h8M12 16v4" 
                stroke-width="2" 
                stroke-linecap="round"
              />
            </svg>
            <!-- Invisible element to ensure button has correct dimensions -->
            <div class="w-6 h-6 invisible">
              <svg class="w-6 h-6" viewBox="0 0 24 24">
                <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
          </button>
        </div>

        <!-- Mobile menu button -->
        <div class="sm:hidden flex items-center">
          <button
            type="button"
            class="inline-flex items-center justify-center p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-white dark:hover:bg-gray-700 focus:outline-none transition-colors duration-200"
            aria-controls="mobile-menu"
            aria-expanded={isMenuOpen}
            on:click={() => isMenuOpen = !isMenuOpen}
          >
            <span class="sr-only">Open main menu</span>
            <!-- Icon when menu is closed -->
            <svg
              class="h-6 w-6 transition-opacity duration-200 {isMenuOpen ? 'opacity-0 absolute' : 'opacity-100'}"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <!-- Icon when menu is open -->
            <svg
              class="h-6 w-6 transition-opacity duration-200 {isMenuOpen ? 'opacity-100' : 'opacity-0 absolute'}"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Mobile menu -->
  <div 
    class="sm:hidden absolute w-full bg-white dark:bg-gray-800 shadow-lg transition-all duration-200 origin-top {isMenuOpen ? 'scale-y-100 opacity-100' : 'scale-y-0 opacity-0'}"
    id="mobile-menu"
  >
    <div class="px-2 pt-2 pb-3 space-y-1">
      <button
        class="w-full text-left px-4 py-3 text-base font-medium rounded-lg transition-all duration-200
               {state.current_page === 'test' ? 
                 'bg-brand text-gray-900 shadow-md' : 
                 'bg-gray-100 text-gray-700 hover:bg-brand hover:text-gray-900 dark:text-gray-200 dark:bg-gray-600 dark:hover:bg-brand dark:hover:text-gray-900'}"
        on:click={() => setPage('test')}
      >
        Test
      </button>
      <button
        class="w-full text-left px-4 py-3 text-base font-medium rounded-lg transition-all duration-200
               {state.current_page === 'data' ? 
                 'bg-brand text-gray-900 shadow-md' : 
                 'bg-gray-100 text-gray-700 hover:bg-brand hover:text-gray-900 dark:text-gray-200 dark:bg-gray-600 dark:hover:bg-brand dark:hover:text-gray-900'}"
        on:click={() => setPage('data')}
      >
        Data
      </button>
      <button
        class="w-full text-left px-4 py-3 text-base font-medium rounded-lg transition-all duration-200
               {state.current_page === 'video' ? 
                 'bg-brand text-gray-900 shadow-md' : 
                 'bg-gray-100 text-gray-700 hover:bg-brand hover:text-gray-900 dark:text-gray-200 dark:bg-gray-600 dark:hover:bg-brand dark:hover:text-gray-900'}"
        on:click={() => setPage('video')}
      >
        Camera
      </button>
    </div>
  </div>
</nav>

<style>
  /* Ensure SVG maintains its aspect ratio */
  img {
    object-fit: contain;
  }
</style> 