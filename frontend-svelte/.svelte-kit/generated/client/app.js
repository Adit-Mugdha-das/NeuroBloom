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
	() => import('./nodes/51'),
	() => import('./nodes/52')
];

export const server_loads = [];

export const dictionary = {
		"/": [2],
		"/admin/dashboard": [3],
		"/admin/departments": [4],
		"/admin/doctors": [5],
		"/admin/patients": [6],
		"/baseline/results": [7],
		"/baseline/tasks/attention": [8],
		"/baseline/tasks/flexibility": [9],
		"/baseline/tasks/planning": [10],
		"/baseline/tasks/processing-speed": [11],
		"/baseline/tasks/visual-scanning": [12],
		"/baseline/tasks/working-memory": [13],
		"/dashboard": [14],
		"/doctor/dashboard": [15],
		"/doctor/messages": [16],
		"/doctor/patient/[id]": [17],
		"/doctor/patient/[id]/reports": [18],
		"/empty-states-preview": [19],
		"/find-doctor": [20],
		"/login": [21],
		"/messages": [22],
		"/progress": [23],
		"/register": [24],
		"/session-summary": [25],
		"/settings": [26],
		"/training": [27],
		"/training/cancellation-test": [28],
		"/training/category-fluency": [29],
		"/training/dccs": [30],
		"/training/digit-span": [31],
		"/training/flanker": [32],
		"/training/gonogo": [33],
		"/training/inspection-time": [34],
		"/training/letter-number-sequencing": [35],
		"/training/multiple-object-tracking": [36],
		"/training/operation-span": [37],
		"/training/pasat": [38],
		"/training/pattern-comparison": [39],
		"/training/plus-minus": [40],
		"/training/sdmt": [41],
		"/training/spatial-span": [42],
		"/training/stockings-of-cambridge": [43],
		"/training/stroop": [44],
		"/training/tower-of-london": [45],
		"/training/trail-making-a": [46],
		"/training/trail-making-b": [47],
		"/training/twenty-questions": [48],
		"/training/useful-field-of-view": [49],
		"/training/verbal-fluency": [50],
		"/training/visual-search": [51],
		"/training/wcst": [52]
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