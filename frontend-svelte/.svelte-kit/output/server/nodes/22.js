

export const index = 22;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/dashboard/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/22.DtOjnSEO.js"];
export const stylesheets = [];
export const fonts = [];
