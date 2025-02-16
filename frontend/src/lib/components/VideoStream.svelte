<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Maximize2, Minimize2 } from 'lucide-svelte';
  
  let videoRef: HTMLVideoElement;
  let containerRef: HTMLDivElement;
  let peerConnection: RTCPeerConnection | null = null;
  let isConnecting = false;
  let error: string | null = null;
  let showControls = false;
  let isFullscreen = false;
  
  const config = {
    iceServers: [
      {
        urls: 'stun:stun.l.google.com:19302'
      }
    ]
  };
  
  async function startStream() {
    try {
      isConnecting = true;
      error = null;
      
      // Create peer connection
      peerConnection = new RTCPeerConnection(config);
      
      // Handle incoming tracks
      peerConnection.ontrack = (event) => {
        if (videoRef && event.streams[0]) {
          videoRef.srcObject = event.streams[0];
        }
      };
      
      // Create and send offer
      const offer = await peerConnection.createOffer();
      await peerConnection.setLocalDescription(offer);
      
      // Send offer to server and get answer
      const response = await fetch('/api/webrtc/offer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sdp: peerConnection.localDescription
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to connect to video stream');
      }
      
      const { sdp: answerSdp } = await response.json();
      await peerConnection.setRemoteDescription(new RTCSessionDescription(answerSdp));
      
      isConnecting = false;
    } catch (err) {
      console.error('Error starting video stream:', err);
      error = err instanceof Error ? err.message : 'Failed to start video stream';
      isConnecting = false;
    }
  }
  
  function stopStream() {
    if (peerConnection) {
      peerConnection.close();
      peerConnection = null;
    }
    if (videoRef && videoRef.srcObject) {
      const tracks = (videoRef.srcObject as MediaStream).getTracks();
      tracks.forEach(track => track.stop());
      videoRef.srcObject = null;
    }
  }
  
  function toggleFullScreen() {
    if (!document.fullscreenElement) {
      containerRef.requestFullscreen().catch((err) => {
        console.error(`Error attempting to enable full-screen mode: ${err.message}`);
      });
    } else {
      document.exitFullscreen();
    }
  }
  
  function handleFullscreenChange() {
    isFullscreen = !!document.fullscreenElement;
  }
  
  onMount(() => {
    startStream();
    document.addEventListener('fullscreenchange', handleFullscreenChange);
  });
  
  onDestroy(() => {
    stopStream();
    document.removeEventListener('fullscreenchange', handleFullscreenChange);
  });
</script>

<div class="relative w-full" 
     bind:this={containerRef}
     on:mouseenter={() => showControls = true}
     on:mouseleave={() => showControls = false}>
  {#if error}
    <div class="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50 rounded-lg">
      <div class="text-white text-center p-4">
        <p class="text-lg font-semibold mb-2">Connection Error</p>
        <p class="text-sm opacity-80">{error}</p>
        <button
          class="mt-4 px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-dark transition-colors"
          on:click={startStream}
        >
          Retry Connection
        </button>
      </div>
    </div>
  {/if}
  
  {#if isConnecting}
    <div class="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50 rounded-lg">
      <div class="text-white text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
        <p>Connecting to camera...</p>
      </div>
    </div>
  {/if}

  <div class="relative w-full aspect-video bg-gray-900 rounded-lg overflow-hidden group">
    <video
      bind:this={videoRef}
      autoplay
      playsinline
      class="w-full h-full object-contain"
    />
    
    <!-- Fullscreen button overlay -->
    <div class="absolute bottom-4 right-4 transition-opacity duration-200 {showControls ? 'opacity-100' : 'opacity-0'}"
         class:opacity-0={!showControls}
         class:opacity-100={showControls}>
      <button
        class="p-2.5 text-white bg-black/70 hover:bg-black/90 rounded-lg transition-colors shadow-lg backdrop-blur-sm"
        on:click={toggleFullScreen}
        title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
      >
        {#if isFullscreen}
          <Minimize2 size={20} />
        {:else}
          <Maximize2 size={20} />
        {/if}
      </button>
    </div>
  </div>
</div>

<style>
  video::-webkit-media-controls {
    display: none !important;
  }
  
  video::-webkit-media-controls-enclosure {
    display: none !important;
  }
</style> 