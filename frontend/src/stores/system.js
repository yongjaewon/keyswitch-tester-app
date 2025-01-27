import { defineStore } from 'pinia'

export const useSystemStore = defineStore('system', {
  state: () => ({
    pin: '',
    systemState: {
      batteryVoltage: 0,
      masterEnable: false,
      cyclesPerMinute: 6
    },
    stations: [
      { number: 1, targetCount: 1000000, currentCount: 0, motorFailures: 0, switchFailures: 0, currentMeasurement: 0, isEnabled: true, status: 'STOPPED' },
      { number: 2, targetCount: 1000000, currentCount: 0, motorFailures: 0, switchFailures: 0, currentMeasurement: 0, isEnabled: true, status: 'STOPPED' },
      { number: 3, targetCount: 1000000, currentCount: 0, motorFailures: 0, switchFailures: 0, currentMeasurement: 0, isEnabled: true, status: 'STOPPED' },
      { number: 4, targetCount: 1000000, currentCount: 0, motorFailures: 0, switchFailures: 0, currentMeasurement: 0, isEnabled: true, status: 'STOPPED' }
    ],
    wsConnected: false
  }),

  actions: {
    setPin(pin) {
      this.pin = pin
    },

    updateSystemState(systemState) {
      this.systemState = systemState
    },

    updateStations(stations) {
      this.stations = stations
    },

    setWsConnected(connected) {
      this.wsConnected = connected
    },

    updateStation(number, data) {
      const index = number - 1
      if (index >= 0 && index < this.stations.length) {
        this.stations[index] = { ...this.stations[index], ...data }
      }
    },

    async startSystem() {
      const response = await fetch(`http://localhost:8000/system/start?pin=${this.pin}`, {
        method: 'POST'
      })
      return response.ok
    },

    async stopSystem() {
      const response = await fetch(`http://localhost:8000/system/stop?pin=${this.pin}`, {
        method: 'POST'
      })
      return response.ok
    },

    async setCycles(cycles) {
      const response = await fetch(`http://localhost:8000/system/cycles?cycles=${cycles}&pin=${this.pin}`, {
        method: 'POST'
      })
      return response.ok
    },

    async toggleStation({ number, enable }) {
      const endpoint = enable ? 'enable' : 'disable'
      const response = await fetch(
        `http://localhost:8000/station/${number}/${endpoint}?pin=${this.pin}`,
        { method: 'POST' }
      )
      return response.ok
    },

    async setTargetCount({ number, target }) {
      const response = await fetch(
        `http://localhost:8000/station/${number}/target?target=${target}&pin=${this.pin}`,
        { method: 'POST' }
      )
      return response.ok
    },

    connectWebSocket() {
      const ws = new WebSocket('ws://localhost:8000/ws')
      
      ws.onopen = () => {
        this.setWsConnected(true)
      }
      
      ws.onclose = () => {
        this.setWsConnected(false)
        // Try to reconnect after 1 second
        setTimeout(() => {
          this.connectWebSocket()
        }, 1000)
      }
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        this.updateSystemState({
          batteryVoltage: data.battery_voltage,
          masterEnable: data.master_enable,
          cyclesPerMinute: data.cycles_per_minute
        })
        this.updateStations(data.stations)
      }
    }
  }
}) 