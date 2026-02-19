/* JsSIP softphone starter (browser)
 *
 * Install:
 *   npm install jssip
 *
 * Usage (example):
 *   import JsSIP from "jssip";
 *   // configure WebSocket interface to Asterisk (PJSIP + WSS recommended)
 */

export function createUA({ websocketUrl, sipUri, password }) {
  // This is a starter stub to match the project structure.
  // You’ll typically configure:
  // - WebSocketInterface(websocketUrl)
  // - new JsSIP.UA({ sockets, uri: sipUri, password })
  // - ua.start()
  return {
    start() {
      throw new Error("Not implemented: wire JsSIP here.");
    },
  };
}

