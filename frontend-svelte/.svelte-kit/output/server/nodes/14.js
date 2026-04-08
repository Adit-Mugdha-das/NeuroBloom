

export const index = 14;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/admin/system-health/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/14.CpBKRiz2.js"];
export const stylesheets = [];
export const fonts = [];
