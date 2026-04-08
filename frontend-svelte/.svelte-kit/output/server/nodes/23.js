

export const index = 23;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/doctor/analytics/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/23.CtSjkmdP.js"];
export const stylesheets = [];
export const fonts = [];
