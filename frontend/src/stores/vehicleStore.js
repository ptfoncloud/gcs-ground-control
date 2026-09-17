import { defineStore } from 'pinia'

export const useVehicleStore = defineStore('vehicle', {
  state: () => ({
    telemetry: {
      altitude: 0,
      ground_speed: 0,
      battery_voltage: 0,
      flight_mode: 'DISCONNECTED',
      armed: false,
      pitch: 0,
      roll: 0,
      yaw: 0
    },
    connected: false,
    leapConnected: false,
    activeGesture: null
  }),
  actions: {
    updateTelemetry(data) {
      this.telemetry = data
      this.connected = true
    }
  }
})
