<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  
  let videoRef: HTMLVideoElement;
  let peerConnection: RTCPeerConnection | null = null;
  let isConnecting = false;
  let error: string | null = null;
  
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
  
  onMount(() => {
    startStream();
  });
  
  onDestroy(() => {
    stopStream();
  });
</script>

<div class="relative w-full">
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

  <div class="relative w-full aspect-video bg-gray-900 rounded-lg overflow-hidden">
    <video
      bind:this={videoRef}
      autoplay
      playsinline
      class="w-full h-full object-contain"
    >
      <track kind="captions" label="captions" srclang="en" default />
    </video>
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