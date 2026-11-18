import { mountAppShell } from '../components/app-shell.js';
import { startRouter } from './router.js';

const root = document.querySelector('#app');

if (!root) {
  throw new Error('KirinDL Web root element was not found.');
}

mountAppShell(root);
startRouter(document.querySelector('#page-view'));
