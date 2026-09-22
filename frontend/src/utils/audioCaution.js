let ctx = null
let isMuted = false
let alarmTimer = null

function getAudioContext() {
  if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)()
  if (ctx.state === 'suspended') ctx.resume()
  return ctx
}

export function playBeep(freq = 800, duration = 0.08) {
  if (isMuted) return
  const audio = getAudioContext()
  const osc = audio.createOscillator()
  const gain = audio.createGain()

  osc.type = 'square'
  osc.frequency.value = freq
  osc.connect(gain)
  gain.connect(audio.destination)

  osc.start()
  // Fade out volume quickly to avoid an annoying click sound
  gain.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + duration)
  osc.stop(audio.currentTime + duration)
}

// Repeat two alternating tones for the warning alarm
export function startAlarm() {
  if (alarmTimer || isMuted) return
  let highTone = false

  alarmTimer = setInterval(() => {
    playBeep(highTone ? 900 : 750, 0.15)
    highTone = !highTone
  }, 250)
}

// Turn the alarm off
export function stopAlarm() {
  clearInterval(alarmTimer)
  alarmTimer = null
}


// Mute toggle switch
export function toggleMute() {
  isMuted = !isMuted
  if (isMuted) stopAlarm()
  return isMuted
}