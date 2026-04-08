

export const index = 30;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/doctor/patients/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/30.ClPh01wP.js"];
export const stylesheets = [];
export const fonts = [];
