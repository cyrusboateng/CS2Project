document.addEventListener('DOMContentLoaded', function() {
    const generateScoreBtn = document.getElementById('generateScoreBtn');
    if (!generateScoreBtn) return;

    generateScoreBtn.addEventListener('click', function() {
        const inputs = document.querySelectorAll('.nihss-input');
        let totalScore = 0;

        // Calculate total score
        inputs.forEach(input => {
            const value = parseInt(input.value) || 0;
            totalScore += value;
        });

        // Update the UI
        const resultDiv = document.getElementById('nihssResult');
        const totalScoreSpan = document.getElementById('totalScore');
        const severityLevelSpan = document.getElementById('severityLevel');

        totalScoreSpan.textContent = totalScore;

        // Determine severity level
        let severityText = '';
        if (totalScore === 0) {
            severityText = 'No Stroke Symptoms';
        } else if (totalScore <= 4) {
            severityText = 'Minor Stroke';
        } else if (totalScore <= 15) {
            severityText = 'Moderate Stroke';
        } else if (totalScore <= 25) {
            severityText = 'Severe Stroke';
        } else {
            severityText = 'Very Severe Stroke';
        }

        severityLevelSpan.textContent = 'Severity: ' + severityText;
        resultDiv.style.display = 'block';
    });

    // Add input validation
    const nihssInputs = document.querySelectorAll('.nihss-input');
    nihssInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = parseInt(this.value);
            const min = parseInt(this.min);
            const max = parseInt(this.max);

            if (value < min) this.value = min;
            if (value > max) this.value = max;
        });
    });
});
