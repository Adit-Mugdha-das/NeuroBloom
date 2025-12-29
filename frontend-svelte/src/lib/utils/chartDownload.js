/**
 * Download a canvas chart as PNG image
 * @param {HTMLCanvasElement} canvas - The canvas element to download
 * @param {string} filename - The name of the downloaded file (without extension)
 */
export function downloadCanvasAsPNG(canvas, filename = 'chart') {
	const link = document.createElement('a');
	link.download = `${filename}.png`;
	link.href = canvas.toDataURL('image/png');
	link.click();
}

/**
 * Download SVG element as PNG image
 * @param {SVGElement} svgElement - The SVG element to download
 * @param {string} filename - The name of the downloaded file (without extension)
 */
export function downloadSVGAsPNG(svgElement, filename = 'chart') {
	const svgData = new XMLSerializer().serializeToString(svgElement);
	const canvas = document.createElement('canvas');
	const ctx = canvas.getContext('2d');
	const img = new Image();
	
	// Get SVG dimensions
	const bbox = svgElement.getBoundingClientRect();
	canvas.width = bbox.width * 2; // 2x for better quality
	canvas.height = bbox.height * 2;
	
	img.onload = function() {
		ctx.scale(2, 2);
		ctx.drawImage(img, 0, 0);
		const link = document.createElement('a');
		link.download = `${filename}.png`;
		link.href = canvas.toDataURL('image/png');
		link.click();
	};
	
	img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
}

/**
 * Download data as CSV file
 * @param {Array<Object>} data - Array of objects to convert to CSV
 * @param {string} filename - The name of the downloaded file (without extension)
 */
export function downloadCSV(data, filename = 'data') {
	if (!data || data.length === 0) return;
	
	// Get headers from first object
	const headers = Object.keys(data[0]);
	
	// Create CSV content
	let csv = headers.join(',') + '\n';
	
	data.forEach(row => {
		const values = headers.map(header => {
			const value = row[header];
			// Escape commas and quotes
			if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
				return `"${value.replace(/"/g, '""')}"`;
			}
			return value;
		});
		csv += values.join(',') + '\n';
	});
	
	// Create download link
	const blob = new Blob([csv], { type: 'text/csv' });
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.download = `${filename}.csv`;
	link.href = url;
	link.click();
	URL.revokeObjectURL(url);
}

/**
 * Download data as JSON file
 * @param {any} data - Data to convert to JSON
 * @param {string} filename - The name of the downloaded file (without extension)
 */
export function downloadJSON(data, filename = 'data') {
	const json = JSON.stringify(data, null, 2);
	const blob = new Blob([json], { type: 'application/json' });
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.download = `${filename}.json`;
	link.href = url;
	link.click();
	URL.revokeObjectURL(url);
}
