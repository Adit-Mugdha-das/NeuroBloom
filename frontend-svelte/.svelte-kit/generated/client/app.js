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
	() => import('./nodes/45'),
	() => import('./nodes/46'),
	() => import('./nodes/47')
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
		"/doctor/messages": [12],
		"/doctor/patient/[id]": [13],
		"/empty-states-preview": [14],
		"/find-doctor": [15],
		"/login": [16],
		"/messages": [17],
		"/progress": [18],
		"/register": [19],
		"/session-summary": [20],
		"/settings": [21],
		"/training": [22],
		"/training/cancellation-test": [23],
		"/training/category-fluency": [24],
		"/training/dccs": [25],
		"/training/digit-span": [26],
		"/training/flanker": [27],
		"/training/gonogo": [28],
		"/training/inspection-time": [29],
		"/training/letter-number-sequencing": [30],
		"/training/multiple-object-tracking": [31],
		"/training/operation-span": [32],
		"/training/pasat": [33],
		"/training/pattern-comparison": [34],
		"/training/plus-minus": [35],
		"/training/sdmt": [36],
		"/training/spatial-span": [37],
		"/training/stockings-of-cambridge": [38],
		"/training/stroop": [39],
		"/training/tower-of-london": [40],
		"/training/trail-making-a": [41],
		"/training/trail-making-b": [42],
		"/training/twenty-questions": [43],
		"/training/useful-field-of-view": [44],
		"/training/verbal-fluency": [45],
		"/training/visual-search": [46],
		"/training/wcst": [47]
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