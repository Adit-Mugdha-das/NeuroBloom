

export const index = 8;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/admin/doctors/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/8.DOfl-7OZ.js"];
export const stylesheets = [];
export const fonts = [];
