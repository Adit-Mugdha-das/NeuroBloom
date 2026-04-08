

export const index = 35;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/login/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/35.Kp_9rc6M.js"];
export const stylesheets = [];
export const fonts = [];
