/**
 * CoreEventBus – лёгкая шина событий на базе EventTarget.
 */
class CoreEventBus extends EventTarget {
  on(event, listener) { this.addEventListener(event, listener); }
  off(event, listener) { this.removeEventListener(event, listener); }
  emit(event, detail = null) { this.dispatchEvent(new CustomEvent(event, { detail })); }
}

export const eventBus = new CoreEventBus();
