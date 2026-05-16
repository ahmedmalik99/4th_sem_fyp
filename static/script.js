let messages = [];
let recognition = null;
let voiceText = '';
let currentSessionId = null;
let selectedRating = 0;

// ── SIDEBAR & DROPDOWN ──
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('active');
    document.getElementById('chatContainer').classList.toggle('sidebar-open');
}

function toggleDropdown() {
    document.getElementById('userDropdown').classList.toggle('active');
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.user-profile')) {
        document.getElementById('userDropdown').classList.remove('active');
    }
});

// ── SESSION MANAGEMENT ──
async function loadSessions() {
    try {
        const res = await fetch('/api/sessions');
        if (!res.ok) return;
        const data = await res.json();
        const list = document.getElementById('sessionList');
        list.innerHTML = data.sessions.map(s => `
            <div class="session-item" onclick="loadSession(${s.id})">
                💬 ${s.session_name}
            </div>
        `).join('');
    } catch(err) {
        console.error('Failed to load sessions:', err);
    }
}

async function loadSession(sessionId) {
    try {
        const res = await fetch(`/api/messages/${sessionId}`);
        if (!res.ok) return;
        const data = await res.json();
        
        currentSessionId = sessionId;
        document.getElementById('welcomeScreen').style.display = 'none';
        document.getElementById('chatContainer').innerHTML = '';
        
        data.messages.forEach(msg => {
            addMsg(msg.sender, msg.content, false);
        });
        
        toggleSidebar();
    } catch(err) {
        console.error('Failed to load session:', err);
    }
}

function newChat() {
    currentSessionId = null;
    messages = [];
    document.getElementById('chatContainer').innerHTML = '';
    document.getElementById('welcomeScreen').style.display = 'flex';
    toggleSidebar();
}

// ── CHAT FUNCTIONS ──
async function sendMsg() {
    const input = document.getElementById('msgInput');
    const text = input.value.trim();
    if (!text) return;

    document.getElementById('welcomeScreen').style.display = 'none';
    input.value = ''; input.style.height = 'auto';
    document.getElementById('sendBtn').disabled = true;

    addMsg('user', text);
    const tid = showTyping();

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                session_id: currentSessionId
            })
        });

        removeTyping(tid);

        if (!res.ok) {
            const e = await res.json();
            addMsg('ai', e.reply || '❌ Server error');
            return;
        }

        const data = await res.json();
        const reply = data.reply;
        currentSessionId = data.session_id;
        
        addMsg('ai', reply, true);
        loadSessions(); // Refresh sidebar

    } catch(e) {
        removeTyping(tid);
        console.error('Connection Error:', e);
        addMsg('ai', '❌ Connection error. Please try again.');
    }

    document.getElementById('sendBtn').disabled = false;
}

function askQ(q) { document.getElementById('msgInput').value = q; sendMsg(); }

function addMsg(role, text, showFeedback = false) {
    const c = document.getElementById('chatContainer');
    const d = document.createElement('div');
    d.className = `message ${role}`;
    const time = new Date().toLocaleTimeString('en-PK',{hour:'2-digit',minute:'2-digit'});
    const label = role === 'ai' ? 'SSUET AI Assistant' : 'You';
    
    let feedbackHTML = '';
    if (showFeedback && role === 'ai') {
        feedbackHTML = `
            <div class="feedback-section">
                <button class="feedback-btn" onclick="rateMessage(this, 'up')">👍 Helpful</button>
                <button class="feedback-btn" onclick="rateMessage(this, 'down')">👎 Not Helpful</button>
            </div>
        `;
    }
    
    d.innerHTML = `
        <div class="avatar ${role==='ai'?'ai':'user-av'}">${role==='ai'?'🤖':'👤'}</div>
        <div class="msg-wrap">
            <div class="msg-label">${label} · ${time}</div>
            <div class="bubble">${fmt(text)}</div>
            ${feedbackHTML}
        </div>`;
    c.appendChild(d);
    c.scrollTop = c.scrollHeight;
}

function fmt(t) {
    return t
        .replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')
        .replace(/\*(.*?)\*/g,'<em>$1</em>')
        .replace(/^### (.*$)/gm,'<strong style="font-size:15px;color:var(--purple-dark)">$1</strong>')
        .replace(/^## (.*$)/gm,'<strong style="font-size:16px;color:var(--purple-dark)">$1</strong>')
        .replace(/^- (.*$)/gm,'&nbsp;&nbsp;• $1')
        .replace(/\n/g,'<br>');
}

function showTyping() {
    const c = document.getElementById('chatContainer');
    const d = document.createElement('div');
    const id = 'typ'+Date.now(); d.id=id; d.className='message ai';
    d.innerHTML = `<div class="avatar ai">🤖</div><div class="msg-wrap"><div class="msg-label">SSUET AI is thinking...</div><div class="bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div></div>`;
    c.appendChild(d); c.scrollTop=c.scrollHeight; return id;
}

function removeTyping(id) { const e=document.getElementById(id); if(e) e.remove(); }

function clearChat() {
    newChat();
}

function handleKey(e) { if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMsg();} }
function autoResize(el) { el.style.height='auto'; el.style.height=Math.min(el.scrollHeight,120)+'px'; }

// ── VOICE INPUT ──
function startVoice() {
    const SR = window.SpeechRecognition||window.webkitSpeechRecognition;
    if(!SR){alert('Voice input requires Chrome browser.');return;}
    recognition=new SR(); recognition.lang='en-US'; recognition.continuous=true; recognition.interimResults=true;
    voiceText='';
    document.getElementById('voiceModal').classList.add('active');
    document.getElementById('voiceTranscript').textContent='Listening...';
    document.getElementById('voiceBtn').classList.add('recording');
    recognition.onresult=(e)=>{
        let f='',i='';
        for(let x=e.resultIndex;x<e.results.length;x++){
            if(e.results[x].isFinal) f+=e.results[x][0].transcript;
            else i+=e.results[x][0].transcript;
        }
        if(f) voiceText+=f;
        document.getElementById('voiceTranscript').textContent=(voiceText+i)||'Listening...';
    };
    recognition.onerror=(e)=>{ document.getElementById('voiceStatus').textContent='Error: '+e.error; };
    recognition.start();
}

function stopVoice() {
    if(recognition) recognition.stop();
    document.getElementById('voiceModal').classList.remove('active');
    document.getElementById('voiceBtn').classList.remove('recording');
    if(voiceText.trim()){ document.getElementById('msgInput').value=voiceText.trim(); sendMsg(); }
}

function speak(text) {
    if(!window.speechSynthesis) return;
    const clean=text.replace(/<[^>]*>/g,'').replace(/[*_#]/g,'').substring(0,280);
    const u=new SpeechSynthesisUtterance(clean);
    u.lang='en-US'; u.rate=0.92; u.pitch=1.05;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
}

// ── FEEDBACK FUNCTIONS ──
function showFeedbackModal() {
    document.getElementById('feedbackModal').classList.add('active');
    document.getElementById('userDropdown').classList.remove('active');
}

function closeFeedbackModal() {
    document.getElementById('feedbackModal').classList.remove('active');
    selectedRating = 0;
}

function setRating(rating) {
    selectedRating = rating;
    const buttons = document.querySelectorAll('#ratingStars .feedback-btn');
    buttons.forEach((btn, i) => {
        btn.classList.toggle('active', i < rating);
    });
}

async function submitFeedback() {
    if (selectedRating === 0) {
        alert('Please select a rating');
        return;
    }
    
    const category = document.getElementById('feedbackCategory').value;
    const comment = document.getElementById('feedbackComment').value;
    
    try {
        const res = await fetch('/api/feedback', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({rating: selectedRating, category, comment})
        });
        
        const data = await res.json();
        if (res.ok) {
            alert(data.message);
            closeFeedbackModal();
            document.getElementById('feedbackComment').value = '';
            setRating(0);
        } else {
            alert(data.error || 'Failed to submit feedback');
        }
    } catch(err) {
        alert('Connection error');
    }
}

// ── TICKET FUNCTIONS ──
function showTicketModal() {
    document.getElementById('ticketModal').classList.add('active');
    document.getElementById('userDropdown').classList.remove('active');
}

function closeTicketModal() {
    document.getElementById('ticketModal').classList.remove('active');
    document.getElementById('ticketSubject').value = '';
    document.getElementById('ticketDescription').value = '';
}

async function submitTicket() {
    const subject = document.getElementById('ticketSubject').value;
    const description = document.getElementById('ticketDescription').value;
    const priority = document.getElementById('ticketPriority').value;
    
    if (!subject || !description) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        const res = await fetch('/api/tickets', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({subject, description, priority})
        });
        
        const data = await res.json();
        if (res.ok) {
            alert(`Ticket #${data.ticket_id} created successfully!`);
            closeTicketModal();
        } else {
            alert(data.error || 'Failed to create ticket');
        }
    } catch(err) {
        alert('Connection error');
    }
}

// ── MESSAGE RATING ──
async function rateMessage(btn, type) {
    btn.classList.add('active');
    const sibling = btn.parentElement.querySelector(`.feedback-btn[onclick*="${type === 'up' ? 'down' : 'up'}"]`);
    if (sibling) sibling.classList.remove('active');
    
    // You can add API call here to save rating
    console.log('Message rated:', type);
}

// ── INITIALIZATION ──
window.addEventListener('DOMContentLoaded', () => {
    loadSessions();
});
