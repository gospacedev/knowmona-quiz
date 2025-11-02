document.addEventListener('DOMContentLoaded', function () {
    let currentQuestion = 1;
    let totalQuestions = 10;
    let correctAnswers = 0;
    let totalXP = 0;

    const CORRECT_ANSWER_XP = 10;
    const WRONG_ANSWER_XP = 7;
    const QUIZ_COMPLETION_XP = 20;

    // Add XP display HTML
    const xpDisplayHTML = `
                        <div class="xp-display position-fixed top-0 end-0 m-3 p-3 bg-dark rounded shadow" style="color: #13e18f;">
                            <div class="d-flex align-items-center">
                                <span class="me-2"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-stars" viewBox="0 0 16 16">
                <path d="M7.657 6.247c.11-.33.576-.33.686 0l.645 1.937a2.89 2.89 0 0 0 1.829 1.828l1.936.645c.33.11.33.576 0 .686l-1.937.645a2.89 2.89 0 0 0-1.828 1.829l-.645 1.936a.361.361 0 0 1-.686 0l-.645-1.937a2.89 2.89 0 0 0-1.828-1.828l-1.937-.645a.361.361 0 0 1 0-.686l1.937-.645a2.89 2.89 0 0 0 1.828-1.828zM3.794 1.148a.217.217 0 0 1 .412 0l.387 1.162c.173.518.579.924 1.097 1.097l1.162.387a.217.217 0 0 1 0 .412l-1.162.387A1.73 1.73 0 0 0 4.593 5.69l-.387 1.162a.217.217 0 0 1-.412 0L3.407 5.69A1.73 1.73 0 0 0 2.31 4.593l-1.162-.387a.217.217 0 0 1 0-.412l1.162-.387A1.73 1.73 0 0 0 3.407 2.31zM10.863.099a.145.145 0 0 1 .274 0l.258.774c.115.346.386.617.732.732l.774.258a.145.145 0 0 1 0 .274l-.774.258a1.16 1.16 0 0 0-.732.732l-.258.774a.145.145 0 0 1-.274 0l-.258-.774a1.16 1.16 0 0 0-.732-.732L9.1 2.137a.145.145 0 0 1 0-.274l.774-.258c.346-.115.617-.386.732-.732z"/>
                                </svg> XP </span>
                                <span id="current-xp">${totalXP}</span>
                            </div>
                        </div>
                    `;
    document.querySelector('.quiz-header').insertAdjacentHTML('afterend', xpDisplayHTML);

    // Add CSS for XP animation
    const style = document.createElement('style');
    style.textContent = `
                        .xp-gain-animation {
                            position: absolute;
                            right: 100%;
                            color: #13e18f;
                            animation: xpFloat 1s ease-out forwards;
                            margin-right: 10px;
                        }
                
                        @keyframes xpFloat {
                            0% {
                                opacity: 1;
                                transform: translateY(0);
                            }
                            100% {
                                opacity: 0;
                                transform: translateY(-20px);
                            }
                        }
                    `;
    document.head.appendChild(style);

    async function saveXP(xpAmount) {
        try {
            const response = await fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    xp_amount: xpAmount
                })
            });

            if (!response.ok) throw new Error('Failed to save XP');

            const data = await response.json();
            if (data.status === 'success') {
                updateXPDisplay(xpAmount);
            }
        } catch (error) {
            console.error('Error saving XP:', error);
        }
    }

    function updateXPDisplay(xpGained) {
        const xpDisplay = document.getElementById('current-xp');
        totalXP += xpGained;
        xpDisplay.textContent = totalXP;

        // Show XP gain animation
        const xpGainElement = document.createElement('div');
        xpGainElement.className = 'xp-gain-animation';
        xpGainElement.textContent = `+${xpGained} XP`;
        document.querySelector('.xp-display').appendChild(xpGainElement);

        setTimeout(() => xpGainElement.remove(), 1000);
    }

    function updateProgressBar() {
        const progress = (currentQuestion / (totalQuestions + 1)) * 100;
        const progressBar = document.querySelector('.progress-bar');
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
    }

    document.querySelectorAll('.choice-card').forEach(card => {
        const radio = card.querySelector('input[type="radio"]');
        const label = card.querySelector('label');

        card.addEventListener('click', function (e) {
            const questionContainer = this.closest('.question-container');
            questionContainer.querySelectorAll('.choice-card').forEach(c => {
                c.classList.remove('selected');
            });
            this.classList.add('selected');
            radio.checked = true;
            e.stopPropagation();
        });

        label.addEventListener('click', function (e) {
            const card = this.closest('.choice-card');
            const questionContainer = card.closest('.question-container');
            questionContainer.querySelectorAll('.choice-card').forEach(c => {
                c.classList.remove('selected');
            });
            card.classList.add('selected');
            radio.checked = true;
            e.stopPropagation();
        });
    });

    function showQuestion(questionNumber) {
        const currentQuestionEl = document.querySelector(`#question-${questionNumber - 1}`);
        const nextQuestionEl = document.querySelector(`#question-${questionNumber}`);

        if (currentQuestionEl) {
            currentQuestionEl.classList.add('slide-out');
            setTimeout(() => {
                currentQuestionEl.style.display = 'none';
            }, 500);
        }

        if (nextQuestionEl) {
            setTimeout(() => {
                nextQuestionEl.style.transform = 'translateX(100%)';
                nextQuestionEl.style.display = 'block';
                setTimeout(() => {
                    nextQuestionEl.style.transform = 'translateX(0)';
                    nextQuestionEl.style.opacity = '1';
                }, 50);
            }, currentQuestionEl ? 500 : 0);
        }

        updateProgressBar();

        const newQuestion = document.querySelector(`#question-${questionNumber}`);
        if (newQuestion) {
            newQuestion.querySelector('.check-answer').disabled = false;
            newQuestion.querySelector('.next-btn').disabled = true;
        }
    }

    document.querySelectorAll('.check-answer').forEach(button => {
        button.addEventListener('click', async function () {
            const button = this;
            button.disabled = true;

            const questionContainer = this.closest('.question-container');
            const selectedRadio = questionContainer.querySelector('input[type="radio"]:checked');
            const feedbackDiv = questionContainer.querySelector('.feedback');
            const feedbackAlert = feedbackDiv.querySelector('.alert');
            const nextButton = questionContainer.querySelector('.next-btn');
            const finishButton = questionContainer.querySelector('.finish-btn');
            const currentQuestionExplanation = feedbackDiv.querySelector('input[id="currentQuestionExplanation"]').value;

            if (!selectedRadio) {
                feedbackDiv.style.display = 'block';
                feedbackAlert.className = 'alert alert-warning';
                feedbackAlert.textContent = 'Please select an answer!';
                button.disabled = false;
                return;
            }

            questionContainer.querySelectorAll('.choice-card').forEach(card => {
                card.classList.remove('correct-answer', 'incorrect-answer');
            });

            const isCorrect = selectedRadio.dataset.correct === 'true';
            feedbackDiv.style.display = 'block';

            if (isCorrect) {
                feedbackAlert.className = 'alert alert-success';
                feedbackAlert.style.color = '#98edc5';
                feedbackAlert.textContent = currentQuestionExplanation;
                selectedRadio.closest('.choice-card').classList.add('correct-answer');
                correctAnswers++;
                await saveXP(CORRECT_ANSWER_XP);
            } else {
                feedbackAlert.className = 'alert alert-danger';
                feedbackAlert.style.color = '#fa919a';
                selectedRadio.closest('.choice-card').classList.add('incorrect-answer');
                const correctChoice = questionContainer.querySelector('input[data-correct="true"]');
                correctChoice.closest('.choice-card').classList.add('correct-answer');
                feedbackAlert.textContent = currentQuestionExplanation;
                await saveXP(WRONG_ANSWER_XP);
            }

            this.style.display = 'none';
            if (nextButton) nextButton.style.display = 'inline-block';
            if (finishButton) finishButton.style.display = 'inline-block';

            if (nextButton) {
                nextButton.disabled = false; // Enable next button only after checking
                nextButton.style.display = 'inline-block';
            }

            button.style.display = 'none'
        });
    });

    document.querySelectorAll('.next-btn').forEach(button => {
        button.addEventListener('click', function () {
            this.disabled = true;
            currentQuestion++;
            showQuestion(currentQuestion);
        });
    });

    const finishBtn = document.querySelector('.finish-btn');
    if (finishBtn) {
        finishBtn.addEventListener('click', async function (e) {
            e.preventDefault();
            document.querySelector('.progress-bar').style.width = '100%';
            document.querySelector('#quiz-form').style.display = 'none';
            document.querySelector('#quiz-summary').style.display = 'block';
            document.querySelector('#correct-count').textContent = correctAnswers;
            await saveXP(QUIZ_COMPLETION_XP);
        });
    }

    updateProgressBar();
});
