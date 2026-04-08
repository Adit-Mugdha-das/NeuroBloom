

export const index = 6;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/admin/dashboard/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/6.BJIuoafw.js"];
export const stylesheets = [];
export const fonts = [];
