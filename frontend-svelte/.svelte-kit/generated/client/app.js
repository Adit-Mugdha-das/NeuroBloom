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
	() => import('./nodes/47'),
	() => import('./nodes/48')
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
		"/doctor/patient/[id]/reports": [14],
		"/empty-states-preview": [15],
		"/find-doctor": [16],
		"/login": [17],
		"/messages": [18],
		"/progress": [19],
		"/register": [20],
		"/session-summary": [21],
		"/settings": [22],
		"/training": [23],
		"/training/cancellation-test": [24],
		"/training/category-fluency": [25],
		"/training/dccs": [26],
		"/training/digit-span": [27],
		"/training/flanker": [28],
		"/training/gonogo": [29],
		"/training/inspection-time": [30],
		"/training/letter-number-sequencing": [31],
		"/training/multiple-object-tracking": [32],
		"/training/operation-span": [33],
		"/training/pasat": [34],
		"/training/pattern-comparison": [35],
		"/training/plus-minus": [36],
		"/training/sdmt": [37],
		"/training/spatial-span": [38],
		"/training/stockings-of-cambridge": [39],
		"/training/stroop": [40],
		"/training/tower-of-london": [41],
		"/training/trail-making-a": [42],
		"/training/trail-making-b": [43],
		"/training/twenty-questions": [44],
		"/training/useful-field-of-view": [45],
		"/training/verbal-fluency": [46],
		"/training/visual-search": [47],
		"/training/wcst": [48]
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