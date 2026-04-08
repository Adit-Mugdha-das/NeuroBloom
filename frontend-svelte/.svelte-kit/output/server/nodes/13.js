

export const index = 13;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/admin/research-data/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/13.DU3y0gdJ.js"];
export const stylesheets = [];
export const fonts = [];
