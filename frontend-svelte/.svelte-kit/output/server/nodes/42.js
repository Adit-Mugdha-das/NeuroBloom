

export const index = 42;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/progress/history/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/42.D5ylhpjD.js"];
export const stylesheets = [];
export const fonts = [];
