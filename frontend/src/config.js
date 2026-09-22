// Backend host resolution.
//
// Previously every component hardcoded `http://localhost:8080` /
// `ws://localhost:8080` directly. That only works when the browser and
// the backend are on the same machine — it breaks the moment the GCS
// console is opened from a laptop/phone on the same network as a
// companion computer running the backend (e.g. FOLLOWER in the field).
//
// Resolution order:
//   1. VITE_API_BASE_URL, if set at build time (for setups where the
//      backend genuinely lives at a fixed, different address).
//   2. Otherwise, derive it from whatever host the page itself was
//      loaded from, assuming the documented default backend port 8080.
//      This means "open the console at http://<drone-ip>:5173" just
//      works without any configuration.
const explicitBase = import.meta.env.VITE_API_BASE_URL
const pageHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost'

export const API_BASE_URL = explicitBase || `http://${pageHost || 'localhost'}:8080`
export const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws')
