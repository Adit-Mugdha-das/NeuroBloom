/** Pure scoring helpers shared by task pages and reproducibility tests. */

export function scoreNBack(correctHits, misses) {
	const targets = correctHits + misses;
	return targets > 0 ? (correctHits / targets) * 100 : 0;
}

export function scoreContinuousPerformance(targetsHit, targetsShown) {
	return targetsShown > 0 ? (targetsHit / targetsShown) * 100 : 0;
}

export function scoreTaskSwitching(totalResponses, totalErrors) {
	return totalResponses > 0 ? ((totalResponses - totalErrors) / totalResponses) * 100 : 0;
}

export function scoreProcessingSpeed(simpleRT, choiceRT, simpleStd, choiceAcc) {
	let simpleScore = 0;
	if (simpleRT <= 190) simpleScore = 36 + ((190 - simpleRT) / 40) * 4;
	else if (simpleRT <= 250) simpleScore = 28 + ((250 - simpleRT) / 60) * 8;
	else if (simpleRT <= 310) simpleScore = 16 + ((310 - simpleRT) / 60) * 12;
	else if (simpleRT <= 400) simpleScore = 4 + ((400 - simpleRT) / 90) * 12;
	else simpleScore = Math.max(0, 4 - ((simpleRT - 400) / 100) * 4);

	let choiceSpeedScore = 0;
	if (choiceRT <= 330) choiceSpeedScore = 27 + ((330 - choiceRT) / 50) * 3;
	else if (choiceRT <= 430) choiceSpeedScore = 21 + ((430 - choiceRT) / 100) * 6;
	else if (choiceRT <= 530) choiceSpeedScore = 12 + ((530 - choiceRT) / 100) * 9;
	else if (choiceRT <= 650) choiceSpeedScore = 3 + ((650 - choiceRT) / 120) * 9;
	else choiceSpeedScore = Math.max(0, 3 - ((choiceRT - 650) / 150) * 3);

	const choiceAccuracyScore = choiceAcc * 10;
	let consistencyScore = 0;
	if (simpleStd <= 30) consistencyScore = 18 + ((30 - simpleStd) / 30) * 2;
	else if (simpleStd <= 50) consistencyScore = 14 + ((50 - simpleStd) / 20) * 4;
	else if (simpleStd <= 80) consistencyScore = 8 + ((80 - simpleStd) / 30) * 6;
	else if (simpleStd <= 120) consistencyScore = 2 + ((120 - simpleStd) / 40) * 6;
	else consistencyScore = Math.max(0, 2 - ((simpleStd - 120) / 60) * 2);

	return Math.min(100, simpleScore + choiceSpeedScore + choiceAccuracyScore + consistencyScore);
}
