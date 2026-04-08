

export const index = 18;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/baseline/tasks/planning/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/18.9RlyETQy.js"];
export const stylesheets = [];
export const fonts = [];
