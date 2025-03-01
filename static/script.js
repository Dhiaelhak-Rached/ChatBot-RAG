document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const uploadStatus = document.getElementById('upload-status');
    const questionsContainer = document.getElementById('questions-container');
    const loading = document.getElementById('loading');
    const fileInput = document.getElementById('pdf-file');
    const fileLabel = document.querySelector('.file-label');

    // Update file label when file is selected
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            fileLabel.textContent = this.files[0].name;
        } else {
            fileLabel.textContent = 'Choose a PDF file';
        }
    });

    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(uploadForm);
        
        if (!fileInput.files.length) {
            showStatus('Please select a PDF file first.', 'error');
            return;
        }
        
        // Clear previous questions and show loading
        questionsContainer.innerHTML = '';
        loading.classList.remove('hidden');
        showStatus('', '');
        
        // Upload the file
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // If upload successful, get the questions
            return fetch('/date');
        })
        .then(response => response.json())
        .then(data => {
            loading.classList.add('hidden');
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Display the questions
            displayQuestions(data.questions);
            showStatus('Questions generated successfully!', 'success');
        })
        .catch(error => {
            loading.classList.add('hidden');
            showStatus(error.message, 'error');
        });
    });

    function displayQuestions(questionsData) {
        questionsContainer.innerHTML = '';
        
        // Check if there are any questions
        if (Object.keys(questionsData).length === 0) {
            questionsContainer.innerHTML = '<p>No questions were generated.</p>';
            return;
        }
        
        // Display each question
        for (const filename in questionsData) {
            const questions = questionsData[filename];
            
            if (questions.length === 0) {
                questionsContainer.innerHTML = '<p>No questions were generated for this PDF.</p>';
                continue;
            }
            
            questions.forEach((question, index) => {
                const questionElement = document.createElement('div');
                questionElement.className = 'question-item';
                questionElement.innerHTML = `<p><strong>Q${index + 1}:</strong> ${question}</p>`;
                questionsContainer.appendChild(questionElement);
            });
        }
    }

    function showStatus(message, type) {
        uploadStatus.textContent = message;
        uploadStatus.className = type;
    }
}); 