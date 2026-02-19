// Minimal SIP Softphone Web UI JavaScript

const numberInput = document.getElementById('numberInput');
const callBtn = document.getElementById('callBtn');
const hangupBtn = document.getElementById('hangupBtn');
const callStatus = document.getElementById('callStatus');

function setStatus(message) {
    if (!callStatus) {
        return;
    }
    callStatus.innerHTML = `<div class="status-idle"><p>${message}</p></div>`;
}

async function makeCall() {
    if (!numberInput) {
        return;
    }

    const number = numberInput.value.trim();
    if (!number) {
        alert('Please enter a number');
        return;
    }

    try {
        const response = await fetch('/make_call', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ number })
        });

        if (!response.ok) {
            const error = await response.json();
            alert(error.detail || 'Call failed');
            return;
        }

        const message = await response.json();
        setStatus(message);

        if (callBtn) callBtn.style.display = 'none';
        if (hangupBtn) hangupBtn.style.display = 'inline-flex';
    } catch (error) {
        console.error('Make call failed:', error);
        alert('Failed to make call');
    }
}

async function hangupCall() {
    try {
        const response = await fetch('/hangup_call', { method: 'POST' });

        if (!response.ok) {
            const error = await response.json();
            alert(error.detail || 'Hangup failed');
            return;
        }

        const message = await response.json();
        setStatus(message);

        if (callBtn) callBtn.style.display = 'inline-flex';
        if (hangupBtn) hangupBtn.style.display = 'none';
    } catch (error) {
        console.error('Hangup failed:', error);
        alert('Failed to hangup call');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (callBtn) {
        callBtn.addEventListener('click', makeCall);
    }

    if (hangupBtn) {
        hangupBtn.addEventListener('click', hangupCall);
        hangupBtn.style.display = 'none';
    }

    if (numberInput) {
        numberInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                makeCall();
            }
        });
    }

    document.querySelectorAll('.dialpad-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            if (!numberInput) {
                return;
            }
            const digit = btn.getAttribute('data-digit') || '';
            numberInput.value += digit;
        });
    });

    setStatus('Ready to call');
});

