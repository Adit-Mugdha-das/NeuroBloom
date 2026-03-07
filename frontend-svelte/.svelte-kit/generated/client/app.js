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
	() => import('./nodes/48'),
	() => import('./nodes/49'),
	() => import('./nodes/50'),
	() => import('./nodes/51')
];

export const server_loads = [];

export const dictionary = {
		"/": [2],
		"/admin/dashboard": [3],
		"/admin/doctors": [4],
		"/admin/patients": [5],
		"/baseline/results": [6],
		"/baseline/tasks/attention": [7],
		"/baseline/tasks/flexibility": [8],
		"/baseline/tasks/planning": [9],
		"/baseline/tasks/processing-speed": [10],
		"/baseline/tasks/visual-scanning": [11],
		"/baseline/tasks/working-memory": [12],
		"/dashboard": [13],
		"/doctor/dashboard": [14],
		"/doctor/messages": [15],
		"/doctor/patient/[id]": [16],
		"/doctor/patient/[id]/reports": [17],
		"/empty-states-preview": [18],
		"/find-doctor": [19],
		"/login": [20],
		"/messages": [21],
		"/progress": [22],
		"/register": [23],
		"/session-summary": [24],
		"/settings": [25],
		"/training": [26],
		"/training/cancellation-test": [27],
		"/training/category-fluency": [28],
		"/training/dccs": [29],
		"/training/digit-span": [30],
		"/training/flanker": [31],
		"/training/gonogo": [32],
		"/training/inspection-time": [33],
		"/training/letter-number-sequencing": [34],
		"/training/multiple-object-tracking": [35],
		"/training/operation-span": [36],
		"/training/pasat": [37],
		"/training/pattern-comparison": [38],
		"/training/plus-minus": [39],
		"/training/sdmt": [40],
		"/training/spatial-span": [41],
		"/training/stockings-of-cambridge": [42],
		"/training/stroop": [43],
		"/training/tower-of-london": [44],
		"/training/trail-making-a": [45],
		"/training/trail-making-b": [46],
		"/training/twenty-questions": [47],
		"/training/useful-field-of-view": [48],
		"/training/verbal-fluency": [49],
		"/training/visual-search": [50],
		"/training/wcst": [51]
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