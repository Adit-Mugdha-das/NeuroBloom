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
	() => import('./nodes/27'),
	() => import('./nodes/28'),
	() => import('./nodes/29'),
	() => import('./nodes/30'),
	() => import('./nodes/31'),
	() => import('./nodes/32'),
	() => import('./nodes/33'),
	() => import('./nodes/34'),
	() => import('./nodes/35'),
	() => import('./nodes/36'),
	() => import('./nodes/37'),
	() => import('./nodes/38'),
	() => import('./nodes/39'),
	() => import('./nodes/40'),
	() => import('./nodes/41'),
	() => import('./nodes/42'),
	() => import('./nodes/43'),
	() => import('./nodes/44'),
	() => import('./nodes/45')
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
		"/doctor/dashboard": [11],
		"/doctor/patient/[id]": [12],
		"/empty-states-preview": [13],
		"/find-doctor": [14],
		"/login": [15],
		"/progress": [16],
		"/register": [17],
		"/session-summary": [18],
		"/settings": [19],
		"/training": [20],
		"/training/cancellation-test": [21],
		"/training/category-fluency": [22],
		"/training/dccs": [23],
		"/training/digit-span": [24],
		"/training/flanker": [25],
		"/training/gonogo": [26],
		"/training/inspection-time": [27],
		"/training/letter-number-sequencing": [28],
		"/training/multiple-object-tracking": [29],
		"/training/operation-span": [30],
		"/training/pasat": [31],
		"/training/pattern-comparison": [32],
		"/training/plus-minus": [33],
		"/training/sdmt": [34],
		"/training/spatial-span": [35],
		"/training/stockings-of-cambridge": [36],
		"/training/stroop": [37],
		"/training/tower-of-london": [38],
		"/training/trail-making-a": [39],
		"/training/trail-making-b": [40],
		"/training/twenty-questions": [41],
		"/training/useful-field-of-view": [42],
		"/training/verbal-fluency": [43],
		"/training/visual-search": [44],
		"/training/wcst": [45]
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