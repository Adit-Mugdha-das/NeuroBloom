export { matchers } from './matchers.js';

export const nodes = [
	() => import('./nodes/0'),
	() => import('./nodes/1'),
	() => import('./nodes/2'),
	() => import('./nodes/3'),
	() => import('./nodes/4'),
	() => import('./nodes/5'),
	() => import('./nodes/6'),
	() => import('./nodes/7'),
	() => import('./nodes/8'),
	() => import('./nodes/9'),
	() => import('./nodes/10'),
	() => import('./nodes/11'),
	() => import('./nodes/12'),
	() => import('./nodes/13'),
	() => import('./nodes/14'),
	() => import('./nodes/15'),
	() => import('./nodes/16'),
	() => import('./nodes/17'),
	() => import('./nodes/18'),
	() => import('./nodes/19'),
	() => import('./nodes/20'),
	() => import('./nodes/21'),
	() => import('./nodes/22'),
	() => import('./nodes/23'),
	() => import('./nodes/24'),
	() => import('./nodes/25'),
	() => import('./nodes/26'),
	() => import('./nodes/27')
];

export const server_loads = [];

export const dictionary = {
		"/": [2],
		"/baseline/results": [3],
		"/baseline/tasks/attention": [4],
		"/baseline/tasks/flexibility": [5],
		"/baseline/tasks/planning": [6],
		"/baseline/tasks/processing-speed": [7],
		"/baseline/tasks/visual-scanning": [8],
		"/baseline/tasks/working-memory": [9],
		"/dashboard": [10],
		"/empty-states-preview": [11],
		"/login": [12],
		"/progress": [13],
		"/register": [14],
		"/session-summary": [15],
		"/training": [16],
		"/training/digit-span": [17],
		"/training/gonogo": [18],
		"/training/inspection-time": [19],
		"/training/letter-number-sequencing": [20],
		"/training/operation-span": [21],
		"/training/pasat": [22],
		"/training/pattern-comparison": [23],
		"/training/sdmt": [24],
		"/training/spatial-span": [25],
		"/training/stroop": [26],
		"/training/trail-making-a": [27]
	};

export const hooks = {
	handleError: (({ error }) => { console.error(error) }),
	
	reroute: (() => {}),
	transport: {}
};

export const decoders = Object.fromEntries(Object.entries(hooks.transport).map(([k, v]) => [k, v.decode]));
export const encoders = Object.fromEntries(Object.entries(hooks.transport).map(([k, v]) => [k, v.encode]));

export const hash = false;

export const decode = (type, value) => decoders[type](value);

export { default as root } from '../root.js';