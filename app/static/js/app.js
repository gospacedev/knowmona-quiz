function selectCard(cardElement, value) {
    const name = cardElement.querySelector('input[type="radio"]').name;
    document.querySelectorAll(`input[name="${name}"]`).forEach(input => {
        input.closest('.radio-card').classList.remove('selected');
    });
    
    cardElement.classList.add('selected');
    const radio = cardElement.querySelector('input[type="radio"]');
    radio.checked = true;
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.add('active');
    document.getElementById('submitButton').disabled = true;
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
    document.getElementById('submitButton').disabled = false;
}

function submitSuggestion(topic) {
    // Set the topic in the input field
    document.getElementById('topicInput').value = topic;

    // Select default values if none are selected
    if (!document.querySelector('input[name="question_difficulty"]:checked')) {
        document.querySelector('input[value="average"]').checked = true;
        document.querySelector('input[value="average"]').closest('.radio-card').classList.add('selected');
    }
    if (!document.querySelector('input[name="tone"]:checked')) {
        document.querySelector('input[value="casual"]').checked = true;
        document.querySelector('input[value="casual"]').closest('.radio-card').classList.add('selected');
    }

    // Submit the form
    document.getElementById('quizForm').submit();
    showLoading();
}

// Handle form submission
document.getElementById('quizForm').addEventListener('submit', function(e) {
    showLoading();

    if (!document.querySelector('input[name="question_difficulty"]:checked')) {
        document.querySelector('input[value="average"]').checked = true;
        document.querySelector('input[value="average"]').closest('.radio-card').classList.add('selected');
    }
    if (!document.querySelector('input[name="tone"]:checked')) {
        document.querySelector('input[value="casual"]').checked = true;
        document.querySelector('input[value="casual"]').closest('.radio-card').classList.add('selected');
    }

    const currentEnergy = "{{ user_energy|default:'0' }}";
    if (parseInt(currentEnergy) < 10) {
        e.preventDefault();
        alert('Not enough energy! Energy resets daily.');
        return;
    }
    
    const badge = document.querySelector('.energy-cost-badge');
    badge.classList.remove('d-none');
    
    // Update energy display immediately
    const newEnergy = parseInt(currentEnergy) - 10;
    document.querySelector('.progress-bar').style.width = newEnergy + '%';
    document.querySelector('.text-light').textContent = newEnergy + '/100';
    
    // Trigger reflow to restart animation
    void badge.offsetWidth;
    
    // Start animation
    badge.style.animation = 'none';
    setTimeout(() => {
        badge.style.animation = 'fadeOutUp 1s ease forwards';
    }, 10);
});

const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));