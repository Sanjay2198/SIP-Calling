// SIP Softphone Web UI JavaScript

let callCheckInterval = null;
let callDuration = 0;
let durationInterval = null;

// DOM Elements
const numberInput = document.getElementById('numberInput');
const callBtn = document.getElementById('callBtn');
const hangupBtn = document.getElementById('hangupBtn');
const answerBtn = document.getElementById('answerBtn');
const muteBtn = document.getElementById('muteBtn');
const holdBtn = document.getElementById('holdBtn');
const callStatus = document.getElementById('callStatus');
const callControls = document.getElementById('callControls');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');

// Contacts
const contactList = document.getElementById('contactList');
const contactsEmpty = document.getElementById('contactsEmpty');
const addContactBtn = document.getElementById('addContactBtn');
const contactName = document.getElementById('contactName');
const contactUri = document.getElementById('contactUri');

// History
const historyList = document.getElementById('historyList');
const historyEmpty = document.getElementById('historyEmpty');

// Tab switching
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// State
let isMuted = false;
let isOnHold = false;

// Initialize
document.addEventListener('DOMContentLoaded', init);

function init() {
    setupEventListeners();
    checkHealth();
    loadContacts();
    loadHistory();
    startCallStatusCheck();
}

function setupEventListeners() {
    // Dial pad
    document.querySelectorAll('.dialpad-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const digit = btn.dataset.digit;
            numberInput.value += digit;
            
            // Send DTMF if in call
            if (callBtn.style.display === 'none') {
                sendDTMF(digit);
            }
        });
    });
    
    // Call actions
    callBtn.addEventListener('click', makeCall);
    hangupBtn.addEventListener('click', hangupCall);
    answerBtn.addEventListener('click', answerCall);
    muteBtn.addEventListener('click', toggleMute);
    holdBtn.addEventListener('click', toggleHold);
    
    // Contacts
    addContactBtn.addEventListener('click', addContact);
    
    // Tabs
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });
    
    // Enter key to call
    numberInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && numberInput.value.trim()) {
            makeCall();
        }
    });
}

// === API Calls ===

async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        if (data.sip_registered) {
            statusDot.classList.remove('offline');
            statusText.textContent = 'Connected';
        } else {
            statusDot.classList.add('offline');
            statusText.textContent = 'Disconnected';
        }
    } catch (error) {
        console.error('Health check failed:', error);
        statusDot.classList.add('offline');
        statusText.textContent = 'Error';
    }
}

async function makeCall() {
    const destination = numberInput.value.trim();
    if (!destination) {
        alert('Please enter a number or SIP URI');
        return;
    }
    
    try {
        const response = await fetch('/api/call/make', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ destination })
        });
        
        if (response.ok) {
            console.log('Call initiated');
            updateUIForCalling(destination);
        } else {
            const error = await response.json();
            alert(`Call failed: ${error.detail}`);
        }
    } catch (error) {
        console.error('Call error:', error);
        alert('Failed to make call');
    }
}

async function hangupCall() {
    try {
        await fetch('/api/call/hangup', { method: 'POST' });
        updateUIForIdle();
    } catch (error) {
        console.error('Hangup error:', error);
    }
}

async function answerCall() {
    try {
        await fetch('/api/call/answer', { method: 'POST' });
        answerBtn.style.display = 'none';
    } catch (error) {
        console.error('Answer error:', error);
    }
}

async function toggleMute() {
    const endpoint = isMuted ? '/api/call/unmute' : '/api/call/mute';
    
    try {
        await fetch(endpoint, { method: 'POST' });
        isMuted = !isMuted;
        muteBtn.classList.toggle('active');
        muteBtn.querySelector('span').textContent = isMuted ? '🔇' : '🔊';
    } catch (error) {
        console.error('Mute toggle error:', error);
    }
}

async function toggleHold() {
    const endpoint = isOnHold ? '/api/call/resume' : '/api/call/hold';
    
    try {
        await fetch(endpoint, { method: 'POST' });
        isOnHold = !isOnHold;
        holdBtn.classList.toggle('active');
        holdBtn.querySelector('span').textContent = isOnHold ? '▶️' : '⏸️';
    } catch (error) {
        console.error('Hold toggle error:', error);
    }
}

async function sendDTMF(digits) {
    try {
        await fetch('/api/call/dtmf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ digits })
        });
    } catch (error) {
        console.error('DTMF error:', error);
    }
}

async function getCallStatus() {
    try {
        const response = await fetch('/api/call/status');
        const status = await response.json();
        return status;
    } catch (error) {
        console.error('Status check error:', error);
        return { active: false };
    }
}

// === Contacts ===

async function loadContacts() {
    try {
        const response = await fetch('/api/contacts');
        const data = await response.json();
        
        if (data.contacts && data.contacts.length > 0) {
            contactsEmpty.style.display = 'none';
            contactList.style.display = 'block';
            contactList.innerHTML = data.contacts.map(contact => `
                <li class="contact-item">
                    <div class="contact-info">
                        <div class="contact-name">${escapeHtml(contact.name)}</div>
                        <div class="contact-uri">${escapeHtml(contact.sip_uri)}</div>
                    </div>
                    <div class="contact-actions">
                        <button class="icon-btn" onclick="callContact('${escapeHtml(contact.sip_uri)}')" title="Call">📞</button>
                        <button class="icon-btn delete" onclick="deleteContact(${contact.id})" title="Delete">🗑️</button>
                    </div>
                </li>
            `).join('');
        } else {
            contactsEmpty.style.display = 'block';
            contactList.style.display = 'none';
        }
    } catch (error) {
        console.error('Load contacts error:', error);
    }
}

async function addContact() {
    const name = contactName.value.trim();
    const uri = contactUri.value.trim();
    
    if (!name || !uri) {
        alert('Please enter both name and SIP URI');
        return;
    }
    
    try {
        const response = await fetch('/api/contacts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, sip_uri: uri })
        });
        
        if (response.ok) {
            contactName.value = '';
            contactUri.value = '';
            loadContacts();
        } else {
            const error = await response.json();
            alert(`Failed to add contact: ${error.detail}`);
        }
    } catch (error) {
        console.error('Add contact error:', error);
        alert('Failed to add contact');
    }
}

async function deleteContact(id) {
    if (!confirm('Delete this contact?')) return;
    
    try {
        await fetch(`/api/contacts/${id}`, { method: 'DELETE' });
        loadContacts();
    } catch (error) {
        console.error('Delete contact error:', error);
    }
}

function callContact(uri) {
    numberInput.value = uri;
    switchTab('contacts');
    makeCall();
}

// === Call History ===

async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.calls && data.calls.length > 0) {
            historyEmpty.style.display = 'none';
            historyList.style.display = 'block';
            historyList.innerHTML = data.calls.map(call => {
                const date = new Date(call.start_time);
                const timeStr = date.toLocaleString();
                const durationStr = formatDuration(call.duration);
                
                return `
                    <li class="history-item">
                        <div class="call-info-item">
                            <div class="call-remote">
                                ${escapeHtml(call.remote_uri)}
                                <span class="call-direction ${call.direction}">${call.direction}</span>
                                <span class="call-status-badge ${call.status}">${call.status}</span>
                            </div>
                            <div class="call-time">${timeStr} • ${durationStr}</div>
                        </div>
                        <div class="history-actions">
                            ${call.recording_path ? `<button class="icon-btn" onclick="playRecording(${call.id})" title="Play Recording">▶️</button>` : ''}
                            <button class="icon-btn" onclick="callContact('${escapeHtml(call.remote_uri)}')" title="Call Back">📞</button>
                        </div>
                    </li>
                `;
            }).join('');
        } else {
            historyEmpty.style.display = 'block';
            historyList.style.display = 'none';
        }
    } catch (error) {
        console.error('Load history error:', error);
    }
}

function playRecording(callId) {
    const audioUrl = `/api/history/${callId}/recording`;
    const audio = new Audio(audioUrl);
    audio.play();
}

// === UI Updates ===

function updateUIForCalling(destination) {
    callStatus.innerHTML = `
        <div class="status-calling">
            <div class="pulse-ring"></div>
            <div class="status-icon">📞</div>
            <div class="call-info">
                <div class="remote-uri">${escapeHtml(destination)}</div>
                <p>Calling...</p>
            </div>
        </div>
    `;
    
    callBtn.style.display = 'none';
    hangupBtn.style.display = 'block';
    callControls.style.display = 'flex';
}

function updateUIForActive(remoteUri, duration) {
    callStatus.innerHTML = `
        <div class="status-active">
            <div class="status-icon">☎️</div>
            <div class="call-info">
                <div class="remote-uri">${escapeHtml(remoteUri)}</div>
                <div class="duration">${formatDuration(duration)}</div>
            </div>
        </div>
    `;
    
    callBtn.style.display = 'none';
    hangupBtn.style.display = 'block';
    callControls.style.display = 'flex';
}

function updateUIForIncoming(remoteUri) {
    callStatus.innerHTML = `
        <div class="status-calling">
            <div class="pulse-ring"></div>
            <div class="status-icon">📲</div>
            <div class="call-info">
                <div class="remote-uri">${escapeHtml(remoteUri)}</div>
                <p>Incoming call...</p>
            </div>
        </div>
    `;
    
    callBtn.style.display = 'none';
    hangupBtn.style.display = 'block';
    answerBtn.style.display = 'block';
    callControls.style.display = 'flex';
}

function updateUIForIdle() {
    callStatus.innerHTML = `
        <div class="status-idle">
            <div class="pulse-ring"></div>
            <div class="status-icon">📵</div>
            <p>Ready to call</p>
        </div>
    `;
    
    callBtn.style.display = 'block';
    hangupBtn.style.display = 'none';
    answerBtn.style.display = 'none';
    callControls.style.display = 'none';
    
    isMuted = false;
    isOnHold = false;
    muteBtn.classList.remove('active');
    holdBtn.classList.remove('active');
    muteBtn.querySelector('span').textContent = '🔊';
    holdBtn.querySelector('span').textContent = '⏸️';
    
    // Reload history
    loadHistory();
}

// === Call Status Monitoring ===

function startCallStatusCheck() {
    callCheckInterval = setInterval(async () => {
        const status = await getCallStatus();
        
        if (status.active) {
            if (status.state === 'CONFIRMED') {
                updateUIForActive(status.remote_uri, status.duration);
            } else if (status.state === 'CALLING' || status.state === 'EARLY') {
                updateUIForCalling(status.remote_uri);
            }
        } else {
            // Check if we were in a call
            if (hangupBtn.style.display === 'block') {
                updateUIForIdle();
            }
        }
    }, 1000);
}

// === Utilities ===

function switchTab(tabName) {
    tabBtns.forEach(btn => {
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    tabContents.forEach(content => {
        if (content.id === tabName + 'Tab') {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
    
    // Reload data when switching tabs
    if (tabName === 'contacts') {
        loadContacts();
    } else if (tabName === 'history') {
        loadHistory();
    }
}

function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '0:00';
    
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Refresh health every 10 seconds
setInterval(checkHealth, 10000);
