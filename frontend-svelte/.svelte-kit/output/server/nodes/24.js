

export const index = 24;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/doctor/dashboard/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/24.CfnRbVw7.js"];
export const stylesheets = [];
export const fonts = [];
