

export const index = 25;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/doctor/messages/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/25.BSQQqixH.js"];
export const stylesheets = [];
export const fonts = [];
