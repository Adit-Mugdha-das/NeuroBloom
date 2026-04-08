

export const index = 16;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/baseline/tasks/attention/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/16.BlQ_eZ-m.js"];
export const stylesheets = [];
export const fonts = [];
