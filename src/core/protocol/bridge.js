export const BRIDGE_CHANNEL = 'kirindl';
export const BRIDGE_VERSION = 1;

export const BRIDGE_MESSAGE_TYPES = Object.freeze([
  'app.open',
  'download.request',
  'download.status',
  'capabilities.request',
  'capabilities.response'
]);

const allowedTypes = new Set(BRIDGE_MESSAGE_TYPES);

export function createBridgeMessage(type, payload = {}) {
  if (!allowedTypes.has(type)) {
    throw new TypeError(`Unsupported KirinDL bridge message type: ${type}`);
  }

  return {
    channel: BRIDGE_CHANNEL,
    version: BRIDGE_VERSION,
    type,
    payload
  };
}

export function isBridgeMessage(value) {
  return Boolean(
    value &&
    typeof value === 'object' &&
    value.channel === BRIDGE_CHANNEL &&
    value.version === BRIDGE_VERSION &&
    allowedTypes.has(value.type) &&
    value.payload !== null &&
    typeof value.payload === 'object'
  );
}
