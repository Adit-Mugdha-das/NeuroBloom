

export const index = 12;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/admin/patients/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/12.BpoDTlE1.js"];
export const stylesheets = [];
export const fonts = [];
