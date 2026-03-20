// ==================== DOM ELEMENTS ====================
const micBtn = document.getElementById('mic-btn');
const statusBadge = document.getElementById('recording-status');
const transcriptionText = document.getElementById('transcription-text');
const aiResponseText = document.getElementById('ai-response-text');
const sentimentIndicator = document.getElementById('sentiment-indicator');
const suggestionsContainer = document.getElementById('suggestions-container');
const conversationLog = document.getElementById('conversation-log');

let recognition;
let isRecording = false;
let lastAIResponse = "";
let isProcessing = false;
let isSpeaking = false;
let pendingDisconnectSummary = null;

// ==================== SPEECH RECOGNITION SETUP ====================
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false; // Process sentence by sentence
    recognition.interimResults = true;
    recognition.lang = 'en-IN';

    recognition.onstart = function() {
        isRecording = true;
        updateUIState('listening');
        transcriptionText.textContent = '';
        transcriptionText.classList.remove('placeholder');
    };

    recognition.onresult = function(event) {
        if (isSpeaking || isProcessing) return; // Prevent infinite Local Audio Echo Loop!

        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }
        
        transcriptionText.innerHTML = finalTranscript + '<span style="color: #8b949e; font-style: italic;">' + interimTranscript + '</span>';
        
        if (finalTranscript.trim() !== '') {
            processCall(finalTranscript.trim());
        }
    };

    recognition.onerror = function(event) {
        console.error("Speech recognition error:", event.error);
        if (event.error !== 'no-speech') {
            updateUIState('error');
            setTimeout(() => updateUIState('inactive'), 1800);
        }
    };

    recognition.onend = function() {
        isRecording = false;
        if (statusBadge.textContent === 'Listening...') {
             updateUIState('inactive');
        }
    };
} else {
    micBtn.disabled = true;
    micBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Browser Not Supported';
    transcriptionText.textContent = "Your browser does not support the Web Speech API. Please use Chrome.";
}

micBtn.addEventListener('click', () => {
    if (isRecording) {
        recognition.stop();
        updateUIState('inactive');
    } else {
        try {
            recognition.start();
        } catch(e) {
            console.error(e);
        }
    }
});

function updateUIState(state) {
    if (state === 'listening') {
        micBtn.innerHTML = '<i class="fas fa-stop"></i><span>Stop Listening</span>';
        micBtn.classList.add('recording');
        micBtn.disabled = false;
        statusBadge.textContent = 'Listening...';
        statusBadge.className = 'status-badge active';
    } else if (state === 'processing') {
        micBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Processing AI...</span>';
        micBtn.classList.remove('recording');
        micBtn.disabled = true;
        statusBadge.textContent = 'Processing AI...';
        statusBadge.className = 'status-badge processing';
    } else if (state === 'inactive') {
        micBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Start Listening</span>';
        micBtn.classList.remove('recording');
        micBtn.disabled = false;
        statusBadge.textContent = 'Inactive';
        statusBadge.className = 'status-badge';
    } else if (state === 'speaking') {
        micBtn.innerHTML = '<i class="fas fa-volume-up"></i><span>AI Speaking...</span>';
        micBtn.classList.remove('recording');
        micBtn.disabled = true;
        statusBadge.textContent = 'Speaking...';
        statusBadge.className = 'status-badge active';
    } else if (state === 'error') {
        statusBadge.textContent = 'Error';
        statusBadge.className = 'status-badge';
        micBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Start Listening</span>';
        micBtn.classList.remove('recording');
        micBtn.disabled = false;
    }
}

// ==================== ADD TO HISTORY ====================
function addToHistory(type, text) {
    if (!conversationLog) return;
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.innerHTML = type === 'user'
        ? '<i class="fas fa-user"></i>'
        : '<i class="fas fa-robot"></i>';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = `<strong>${type === 'user' ? 'You (Human)' : 'AI Assistant'}</strong> ${text}`;

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
    conversationLog.appendChild(msgDiv);
    conversationLog.scrollTop = conversationLog.scrollHeight;
    msgDiv.classList.add('fade-in');
}

// ==================== PROCESS USER SPEECH ====================
async function processCall(text) {
    if (isProcessing || isSpeaking) return;
    isProcessing = true;

    addToHistory('user', text);
    updateUIState('processing');
    
    try {
        const response = await fetch("http://127.0.0.1:5001/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: "web_user", message: text }) // Using web_user explicitly per requirements
        });

        if (!response.ok) throw new Error("Network response was not ok");
        
        const data = await response.json();
        
        if (data.suggestions && data.suggestions.includes("End call")) {
            pendingDisconnectSummary = data.summary;
        }

        // Update UI organically
        updateDashboard(data);
        addToHistory('ai', data.response || "Sorry, I couldn't generate a response.");
        
        // Speak AI synthesis
        speakText(data.response || "Sorry, something went wrong.");
        
    } catch (error) {
        console.error("Error communicating with backend:", error);
        const errorMsg = "Could not fetch AI response. Please try speaking again.";
        aiResponseText.textContent = errorMsg;
        aiResponseText.classList.remove('placeholder');
        addToHistory('ai', errorMsg);
        updateUIState('inactive');
    } finally {
        isProcessing = false;
    }
}

// ==================== UPDATE DASHBOARD ====================
function updateDashboard(data) {
    try {
        if (data && data.response && String(data.response).trim() !== "") {
            lastAIResponse = String(data.response);
            requestAnimationFrame(() => {
                aiResponseText.innerText = lastAIResponse;
                aiResponseText.classList.remove('placeholder');
                // Force reflow
                aiResponseText.classList.remove('fade-in');
                void aiResponseText.offsetWidth; 
                aiResponseText.classList.add('fade-in');
            });
        }

        const sentimentLower = (data.sentiment || "Neutral").toLowerCase();
        let icon = "fa-minus";
        let colorClass = "neutral";
        
        if (sentimentLower === 'positive') {
            icon = "fa-smile";
            colorClass = "positive";
        } else if (sentimentLower === 'negative') {
            icon = "fa-frown";
            colorClass = "negative";
        }

        sentimentIndicator.className = `sentiment-chip ${colorClass} fade-in`;
        sentimentIndicator.innerHTML = `<i class="fas ${icon}"></i> ${data.sentiment || "Neutral"}`;

        suggestionsContainer.innerHTML = '';
        if (data.suggestions && Array.isArray(data.suggestions) && data.suggestions.length > 0) {
            data.suggestions.forEach(sug => {
                const span = document.createElement('span');
                span.className = 'suggestion-tag fade-in';
                span.innerHTML = `<i class="fas fa-lightbulb" style="color:var(--accent-yellow);margin-right:4px;"></i> ${String(sug)}`;
                suggestionsContainer.appendChild(span);
            });
        } else {
            suggestionsContainer.innerHTML = '<span class="placeholder">No active suggestions.</span>';
        }
    } catch (e) {
        console.error("UI Render Exception", e);
    }
}

// ==================== TEXT-TO-SPEECH ====================
let currentUtterance = null;

function speakText(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        isSpeaking = true;
        
        currentUtterance = new SpeechSynthesisUtterance(text);
        currentUtterance.lang = 'en-US';
        currentUtterance.rate = 1.0;
        
        currentUtterance.onstart = () => {
            updateUIState('speaking');
            aiResponseText.classList.add('speaking');
        };

        currentUtterance.onend = () => {
            isSpeaking = false;
            requestAnimationFrame(() => {
                updateUIState('inactive');
                aiResponseText.classList.remove('speaking');
                
                if (pendingDisconnectSummary) {
                    aiResponseText.innerHTML = `<strong>☎️ Call disconnect</strong><br><br><span style="color:var(--accent-glow);"><strong>Session Summary:</strong></span> ${pendingDisconnectSummary}`;
                    micBtn.disabled = true;
                    micBtn.innerHTML = '<i class="fas fa-phone-slash"></i><span>Call Ended</span>';
                    micBtn.style.background = '#64748b';
                    micBtn.style.boxShadow = 'none';
                    statusBadge.textContent = 'Disconnected';
                    statusBadge.className = 'status-badge';
                    
                    try {
                        fetch("http://127.0.0.1:5001/clear", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ user_id: "web_user" })
                        });
                    } catch (e) {}
                    
                    pendingDisconnectSummary = null;
                }
            });
        };

        currentUtterance.onerror = (e) => {
            isSpeaking = false;
            console.error("Speech synthesis error", e);
            updateUIState('inactive');
            aiResponseText.classList.remove('speaking');
        };
        
        window.speechSynthesis.speak(currentUtterance);
    } else {
        updateUIState('inactive');
    }
}

// ==================== MANUAL CLEAR UI ====================
const clearBtn = document.getElementById('clear-btn');
if (clearBtn) {
    clearBtn.addEventListener('click', async () => {
        if (conversationLog) conversationLog.innerHTML = '';
        lastAIResponse = '';
        aiResponseText.textContent = 'AI response will appear here...';
        aiResponseText.classList.add('placeholder');
        transcriptionText.textContent = 'Speak now... your words will appear here and in history';
        transcriptionText.classList.add('placeholder');
        suggestionsContainer.innerHTML = '<span class="placeholder">No actionable suggestions yet.</span>';
        sentimentIndicator.className = 'sentiment-chip neutral';
        sentimentIndicator.innerHTML = '<i class="fas fa-minus"></i> Neutral';
        
        micBtn.disabled = false;
        micBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Start Listening</span>';
        micBtn.style.background = '';
        micBtn.style.boxShadow = '';
        pendingDisconnectSummary = null;
        
        try {
            await fetch("http://127.0.0.1:5001/clear", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: "web_user" })
            });
        } catch (e) {
            console.error("Failed to clear backend memory", e);
        }
    });
}

// Init
updateUIState('inactive');

// ==================== LIVE TWILIO MONITORING ====================
let currentHistoryLength = 0;
let lastSessionId = null;

setInterval(async () => {
    // Pause if actively speaking or manually dictating to avoid visual clashes
    if (isRecording || isSpeaking || isProcessing) return;

    try {
        const res = await fetch("http://127.0.0.1:5001/live-monitor");
        if (!res.ok) return;
        const data = await res.json();
        
        if (data.error) return;
        
        // Avoid overriding Web Dashboard's own local testing sessions!
        if (data.phone === "web_user") return;
        
        // Fresh Call Reset
        if (lastSessionId !== data.session_id) {
            lastSessionId = data.session_id;
            currentHistoryLength = 0;
            pendingDisconnectSummary = null;
            
            // Clean UI
            if (conversationLog) {
                conversationLog.innerHTML = `<div style="text-align:center; color:var(--text-secondary); font-size:0.85rem; margin-bottom:1rem; padding:6px; background:#e2e8f0; border-radius:6px; font-weight:600;"><i class="fas fa-satellite-dish" style="color:#3b82f6;"></i> Live Outbound/Inbound Call Detected: ${data.phone}</div>`;
            }
            micBtn.disabled = true;
            micBtn.innerHTML = '<i class="fas fa-phone-volume fa-shake"></i><span>Twilio Line Active</span>';
            micBtn.style.background = '#f59e0b';
            micBtn.style.boxShadow = '0 0 15px rgba(245,158,11,0.4)';
            statusBadge.textContent = 'Monitoring Call';
            statusBadge.className = 'status-badge processing';
        }
        
        // Live Sentiment Extraction
        const sentimentLower = (data.sentiment || "neutral").toLowerCase();
        let icon = "fa-minus"; let colorClass = "neutral";
        if (sentimentLower === 'positive') { icon = "fa-smile"; colorClass = "positive"; }
        else if (sentimentLower === 'negative') { icon = "fa-frown"; colorClass = "negative"; }
        
        sentimentIndicator.className = `sentiment-chip ${colorClass} fade-in`;
        sentimentIndicator.innerHTML = `<i class="fas ${icon}"></i> ${data.sentiment || "Neutral"}`;
        
        // Inject new lines chronologically
        if (data.history && data.history.length > currentHistoryLength) {
            for (let i = currentHistoryLength; i < data.history.length; i++) {
                const line = data.history[i];
                if (line.startsWith("User:")) {
                    let userText = line.replace("User:", "").trim();
                    addToHistory('user', userText);

                    // Push implicitly to Live Dictation Box too!
                    requestAnimationFrame(() => {
                        if (transcriptionText) {
                            transcriptionText.innerHTML = `<span style="color:var(--accent-glow);font-weight:600;">User:</span> ${userText}`;
                            transcriptionText.classList.remove('placeholder');
                        }
                    });
                } else if (line.startsWith("AI:")) {
                    let aiText = line.replace("AI:", "").trim();
                    addToHistory('ai', aiText);
                    
                    // Natively swap inside the Live Assistant box!
                    requestAnimationFrame(() => {
                        aiResponseText.innerText = aiText;
                        aiResponseText.classList.remove('placeholder');
                        aiResponseText.classList.remove('fade-in');
                        void aiResponseText.offsetWidth; // force css reflow
                        aiResponseText.classList.add('fade-in');
                    });
                }
            }
            currentHistoryLength = data.history.length;
        }

        // Live Suggestions Extractor
        if (data.suggestions && Array.isArray(data.suggestions) && data.suggestions.length > 0) {
            if (suggestionsContainer) {
                let newSugHTML = '';
                data.suggestions.forEach(sug => {
                    newSugHTML += `<span class="suggestion-tag fade-in"><i class="fas fa-lightbulb" style="color:var(--accent-yellow);margin-right:4px;"></i> ${String(sug)}</span>`;
                });
                // Only rewrite DOM if it changed to prevent CSS flashing
                if (suggestionsContainer.innerHTML !== newSugHTML) {
                    suggestionsContainer.innerHTML = newSugHTML;
                }
            }
        }
        
        // Completion Handler (Only complete if resolved)
        if (data.status === "resolved" && !pendingDisconnectSummary) {
            pendingDisconnectSummary = data.summary;
            
            setTimeout(() => {
                aiResponseText.innerHTML = `<strong>☎️ Call disconnect</strong><br><br><span style="color:var(--accent-glow);"><strong>Final Call Summary:</strong></span> ${pendingDisconnectSummary}`;
                micBtn.innerHTML = '<i class="fas fa-phone-slash"></i><span>Call Ended</span>';
                micBtn.style.background = '#64748b';
                micBtn.style.boxShadow = 'none';
                statusBadge.textContent = 'Disconnected';
                statusBadge.className = 'status-badge';
            }, 1000);
        }
        
    } catch(e) {}
}, 2000);
