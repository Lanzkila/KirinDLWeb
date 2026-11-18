import test from 'node:test';
import assert from 'node:assert/strict';
import {
  BRIDGE_CHANNEL,
  BRIDGE_VERSION,
  createBridgeMessage,
  isBridgeMessage
} from '../../src/core/protocol/bridge.js';

test('creates a versioned KirinDL bridge message', () => {
  const message = createBridgeMessage('download.request', { url: 'https://example.com/video' });

  assert.equal(message.channel, BRIDGE_CHANNEL);
  assert.equal(message.version, BRIDGE_VERSION);
  assert.equal(message.type, 'download.request');
  assert.equal(message.payload.url, 'https://example.com/video');
});

test('rejects an unknown message type', () => {
  assert.throws(() => createBridgeMessage('shell.execute'), TypeError);
});

test('validates a known message envelope', () => {
  assert.equal(isBridgeMessage(createBridgeMessage('app.open')), true);
  assert.equal(isBridgeMessage({ channel: 'other', version: 1, type: 'app.open', payload: {} }), false);
  assert.equal(isBridgeMessage({ channel: 'kirindl', version: 99, type: 'app.open', payload: {} }), false);
});
