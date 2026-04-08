

export const index = 32;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/doctor/reports/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/32.DiJoZkBR.js"];
export const stylesheets = [];
export const fonts = [];
