

export const index = 10;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/admin/messages/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/10.bSB9m6_g.js"];
export const stylesheets = [];
export const fonts = [];
