// Application State
let selectedFile = null;
let recognition = null;
let isRecording = false;

// DOM Elements
const recordBtn = document.getElementById('record-btn');
const recordBtnText = document.getElementById('record-btn-text');
const audioWave = document.getElementById('audio-wave');
const transcriptInput = document.getElementById('transcript-input');

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const previewContainer = document.getElementById('preview-container');
const imagePreview = document.getElementById('image-preview');
const removeImgBtn = document.getElementById('remove-img-btn');
const sampleImgBtn = document.getElementById('sample-img-btn');

const analyzeBtn = document.getElementById('analyze-btn');
const analyzeBtnText = document.getElementById('analyze-btn-text');
const analyzeLoader = document.getElementById('analyze-loader');

const emptyStateView = document.getElementById('empty-state-view');
const errorView = document.getElementById('error-view');
const errorMessage = document.getElementById('error-message');
const resultsDisplayView = document.getElementById('results-display-view');

const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');

const resultStatus = document.getElementById('result-status');
const statusBadgeCard = document.getElementById('status-badge-card');
const verdictSvgIcon = document.getElementById('verdict-svg-icon');
const resultLoss = document.getElementById('result-loss');
const resultConfidence = document.getElementById('result-confidence');
const confidenceCircle = document.getElementById('confidence-circle');
const resultRationale = document.getElementById('result-rationale');
const resultAction = document.getElementById('result-action');
const resultTxHash = document.getElementById('result-tx-hash');
const resultTimestamp = document.getElementById('result-timestamp');

// Inline SVGs for Verdict Badge
const approvedIconSvg = `
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
    <polyline points="22 4 12 14.01 9 11.01"/>
</svg>
`;

const rejectedIconSvg = `
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="15" y1="9" x2="9" y2="15"/>
    <line x1="9" y1="9" x2="15" y2="15"/>
</svg>
`;

// Initialize Page
window.addEventListener('DOMContentLoaded', () => {
    initSpeechRecognition();
    checkBackendConnection();
});

// Check Server Connectivity on Startup
async function checkBackendConnection() {
    try {
        // Ping root to verify backend is up
        const response = await fetch('/');
        if (response.ok) {
            statusIndicator.className = 'status-dot pulse';
            statusText.innerText = 'SYSTEM ONLINE';
        } else {
            setSystemOffline();
        }
    } catch (e) {
        setSystemOffline();
    }
}

function setSystemOffline() {
    statusIndicator.className = 'status-dot disconnected';
    statusText.innerText = 'OFFLINE MODE';
}

// -------------------------------------------------------------
// Speech Recognition Module (Web Speech API)
// -------------------------------------------------------------
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        recordBtn.style.display = 'none';
        console.warn('Web Speech API is not supported in this browser.');
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isRecording = true;
        recordBtn.classList.add('recording');
        recordBtnText.innerText = 'Stop Speech Dictation';
        audioWave.classList.add('active');
    };

    recognition.onend = () => {
        isRecording = false;
        recordBtn.classList.remove('recording');
        recordBtnText.innerText = 'Start Speech Dictation';
        audioWave.classList.remove('active');
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopRecording();
    };

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }

        if (finalTranscript) {
            // Append final speech segment to text input
            const separator = transcriptInput.value ? ' ' : '';
            transcriptInput.value += separator + finalTranscript.trim();
        }
    };

    recordBtn.addEventListener('click', () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });
}

function startRecording() {
    if (recognition) {
        recognition.start();
    }
}

function stopRecording() {
    if (recognition) {
        recognition.stop();
    }
}

// -------------------------------------------------------------
// Drag & Drop / Image Selection Module
// -------------------------------------------------------------
// Drag events
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('dragover');
    }, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('dragover');
    }, false);
});

// Drop file handler
dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
        handleFileSelection(files[0]);
    }
});

// File input select handler
fileInput.addEventListener('change', (e) => {
    if (fileInput.files.length > 0) {
        handleFileSelection(fileInput.files[0]);
    }
});

// Open file selector when clicking the dropzone (except remove btn)
dropZone.addEventListener('click', (e) => {
    if (e.target !== removeImgBtn && !removeImgBtn.contains(e.target)) {
        fileInput.click();
    }
});

function handleFileSelection(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please drop an image file (PNG/JPG).');
        return;
    }
    selectedFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        previewContainer.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

// Remove selected image
removeImgBtn.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = '';
    imagePreview.src = '';
    previewContainer.style.display = 'none';
});

// Use Sample Image Button
sampleImgBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    try {
        sampleImgBtn.disabled = true;
        sampleImgBtn.innerHTML = 'Loading sample...';
        
        const response = await fetch('/static/test_cargo.jpg');
        if (!response.ok) {
            throw new Error('Failed to download test_cargo.jpg. Make sure the file exists.');
        }
        
        const blob = await response.blob();
        const file = new File([blob], 'test_cargo.jpg', { type: 'image/jpeg' });
        handleFileSelection(file);
    } catch (err) {
        alert('Error loading sample image: ' + err.message);
    } finally {
        sampleImgBtn.disabled = false;
        sampleImgBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21 15 16 10 5 21"/>
            </svg>
            Use Sample Cargo Image (test_cargo.jpg)
        `;
    }
});

// -------------------------------------------------------------
// Run Compliance Analysis Route call
// -------------------------------------------------------------
analyzeBtn.addEventListener('click', async () => {
    const transcriptText = transcriptInput.value.trim();

    // Validation
    if (!transcriptText) {
        alert('Please provide a driver voice transcript or text.');
        transcriptInput.focus();
        return;
    }

    if (!selectedFile) {
        alert('Please upload a cargo photo or select the sample image.');
        return;
    }

    // Set Loading State
    setLoadingState(true);
    emptyStateView.style.display = 'none';
    errorView.style.display = 'none';
    resultsDisplayView.style.display = 'none';

    // Prepare Multipart Form Data
    const formData = new FormData();
    formData.append('driver_transcript', transcriptText);
    formData.append('cargo_image', selectedFile);

    try {
        const response = await fetch('/api/v1/compliance/verify', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Server encountered an error during compliance auditing.');
        }

        renderAuditResults(data);
    } catch (err) {
        showError(err.message);
    } finally {
        setLoadingState(false);
    }
});

function setLoadingState(loading) {
    if (loading) {
        analyzeBtn.disabled = true;
        analyzeBtnText.innerText = 'Analyzing compliance criteria...';
        analyzeLoader.style.display = 'block';
    } else {
        analyzeBtn.disabled = false;
        analyzeBtnText.innerText = 'Execute Compliance Verification';
        analyzeLoader.style.display = 'none';
    }
}

function showError(msg) {
    errorMessage.innerText = msg;
    errorView.style.display = 'block';
    emptyStateView.style.display = 'none';
    resultsDisplayView.style.display = 'none';
}

function renderAuditResults(results) {
    // 1. Verdict card
    const status = results.status.toUpperCase();
    resultStatus.innerText = status;
    
    // Clear classes
    statusBadgeCard.className = 'verdict-card';
    if (status === 'APPROVED') {
        statusBadgeCard.classList.add('approved');
        verdictSvgIcon.innerHTML = approvedIconSvg;
    } else {
        statusBadgeCard.classList.add('rejected');
        verdictSvgIcon.innerHTML = rejectedIconSvg;
    }

    // 2. Financial Loss
    const formattedLoss = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(results.estimated_loss);
    resultLoss.innerText = formattedLoss;

    // 3. Confidence score circular animation
    // Map score (typically 0.0 to 1.0, or 0 to 100)
    let rawScore = results.confidence_score;
    if (rawScore <= 1.0) {
        rawScore = Math.round(rawScore * 100);
    } else {
        rawScore = Math.round(rawScore);
    }
    rawScore = Math.min(100, Math.max(0, rawScore)); // clamp between 0 and 100
    
    resultConfidence.innerText = `${rawScore}%`;
    
    // Set circle offset animation (dasharray = "score, 100")
    confidenceCircle.setAttribute('stroke-dasharray', `${rawScore}, 100`);

    // 4. Compliance rationale
    resultRationale.innerText = results.legal_rationale || 'No detail available.';

    // 5. Blockchain integration properties
    resultAction.innerText = results.action_executed || 'PENDING_MANUAL_REVIEW';
    
    // Generate static mock hash
    const randomHash = '0x' + Array.from({length: 40}, () => Math.floor(Math.random()*16).toString(16)).join('');
    resultTxHash.innerText = randomHash.substring(0, 14) + '...' + randomHash.substring(34);
    resultTxHash.title = randomHash;

    // Set Timestamp
    const now = new Date();
    resultTimestamp.innerText = now.toLocaleString();

    // Show output
    resultsDisplayView.style.display = 'flex';
}
