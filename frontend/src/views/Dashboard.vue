<script setup>
import { onMounted } from 'vue'
import { useSystemStore } from '../stores/system'

const systemStore = useSystemStore()

onMounted(() => {
  systemStore.connectWebSocket()
})

const toggleSystem = async () => {
  if (systemStore.systemState.masterEnable) {
    await systemStore.stopSystem()
  } else {
    await systemStore.startSystem()
  }
}

const toggleStation = async (number, enable) => {
  await systemStore.toggleStation({ number, enable })
}
</script>

<template>
  <div class="dashboard">
    <header class="system-header">
      <div class="system-info">
        <div class="battery">
          Battery: {{ systemStore.systemState.batteryVoltage.toFixed(1) }}V
        </div>
        <div class="cycles">
          Cycles/Min: {{ systemStore.systemState.cyclesPerMinute }}
        </div>
      </div>
      <div class="system-controls">
        <button 
          class="start-stop" 
          :class="{ 'running': systemStore.systemState.masterEnable }"
          @click="toggleSystem"
        >
          {{ systemStore.systemState.masterEnable ? 'STOP' : 'START' }}
        </button>
      </div>
    </header>

    <div class="stations-grid">
      <div 
        v-for="station in systemStore.stations" 
        :key="station.number"
        class="station-card"
        :class="{ 
          'disabled': !station.isEnabled,
          'running': station.status === 'RUNNING',
          'error': station.status === 'ERROR'
        }"
      >
        <div class="station-header">
          <h3>Station {{ station.number }}</h3>
          <label class="switch">
            <input 
              type="checkbox" 
              :checked="station.isEnabled"
              @change="toggleStation(station.number, !station.isEnabled)"
            >
            <span class="slider"></span>
          </label>
        </div>

        <div class="station-stats">
          <div class="count">
            <div class="current">{{ station.currentCount }}</div>
            <div class="target">/ {{ station.targetCount }}</div>
          </div>
          <div class="failures">
            <div class="motor">Motor: {{ station.motorFailures }}</div>
            <div class="switch">Switch: {{ station.switchFailures }}</div>
          </div>
          <div class="current-draw">
            Current: {{ station.currentMeasurement.toFixed(2) }}A
          </div>
        </div>

        <div class="station-status">
          Status: {{ station.status }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
}

.system-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  margin-bottom: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.system-info {
  display: flex;
  gap: 2rem;
  font-size: 1.2rem;
}

.start-stop {
  padding: 0.75rem 2rem;
  font-size: 1.2rem;
  border: none;
  border-radius: 4px;
  background: #28a745;
  color: white;
  cursor: pointer;
}

.start-stop.running {
  background: #dc3545;
}

.start-stop:hover {
  opacity: 0.9;
}

.stations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.station-card {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.station-card.disabled {
  opacity: 0.7;
}

.station-card.running {
  border: 2px solid #28a745;
}

.station-card.error {
  border: 2px solid #dc3545;
}

.station-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.station-header h3 {
  margin: 0;
}

.station-stats .count {
  display: flex;
  align-items: baseline;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.station-stats .count .target {
  margin-left: 0.5rem;
  font-size: 1rem;
  color: #666;
}

.station-stats .failures {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
  color: #dc3545;
}

.station-stats .current-draw {
  color: #666;
}

.station-status {
  margin-top: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid #eee;
}

/* Toggle switch styles */
.switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 34px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.switch .slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 34px;
}

.switch .slider:before {
  position: absolute;
  content: "";
  height: 26px;
  width: 26px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

.switch input:checked + .slider {
  background-color: #2196F3;
}

.switch input:checked + .slider:before {
  transform: translateX(26px);
}
</style> 