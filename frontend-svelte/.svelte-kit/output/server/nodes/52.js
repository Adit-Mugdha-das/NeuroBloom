

export const index = 52;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/training/dual-n-back/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/52.C7kZvejq.js"];
export const stylesheets = [];
export const fonts = [];
