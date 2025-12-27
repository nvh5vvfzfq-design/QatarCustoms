const fileInput = document.getElementById('fileInput');
if (fileInput) {
    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        const statusDiv = document.getElementById('uploadStatus');
        statusDiv.textContent = 'Uploading...';

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (response.ok) {
                statusDiv.textContent = 'Uploaded: ' + result.filename;
                console.log("Adding source:", result.filename);
                addSourceToSidebar(result.filename);
            } else {
                console.error("Upload error:", result);
                statusDiv.textContent = 'Error uploading.';
            }
        } catch (err) {
            console.error("Upload exception:", err);
            statusDiv.textContent = 'Upload failed.';
        }
    });
}

function addSourceToSidebar(filename) {
    const list = document.getElementById('sourceList');
    const item = document.createElement('div');
    item.className = 'source-item';
    // item.textContent handled below
    item.style.padding = '8px 12px';
    item.style.borderRadius = '8px';
    item.style.fontSize = '14px';
    item.style.marginTop = '8px';
    item.style.background = '#f1f3f4';

    // Add text container
    const textSpan = document.createElement('span');
    textSpan.textContent = filename;
    textSpan.style.flex = '1';
    textSpan.style.overflow = 'hidden';
    textSpan.style.textOverflow = 'ellipsis';
    textSpan.style.whiteSpace = 'nowrap';
    item.appendChild(textSpan);

    // Delete button (Admin only)
    if (typeof IS_ADMIN !== 'undefined' && IS_ADMIN) {
        const delBtn = document.createElement('span');
        delBtn.className = 'material-icons';
        delBtn.textContent = 'delete';
        delBtn.style.fontSize = '18px';
        delBtn.style.color = '#8A1538';
        delBtn.style.cursor = 'pointer';
        delBtn.title = 'Delete Document';

        delBtn.onclick = async (e) => {
            e.stopPropagation();
            if (confirm(`Delete ${filename}?`)) {
                try {
                    await fetch(`/documents/${filename}`, { method: 'DELETE' });
                    item.remove();
                } catch (err) {
                    console.error('Delete failed', err);
                }
            }
        };
        item.appendChild(delBtn);
    }

    list.appendChild(item);
}

// Fetch existing documents on load
async function fetchDocuments() {
    console.log("Fetching documents...");
    try {
        const response = await fetch('/documents');
        const data = await response.json();
        console.log("Documents received:", data);
        const list = document.getElementById('sourceList');
        if (list) {
            list.innerHTML = ''; // Clear existing
            data.documents.forEach(doc => addSourceToSidebar(doc));
        }
    } catch (err) {
        console.error("Failed to fetch documents", err);
    }
}

// Ensure DOM is fully loaded before attaching
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

function init() {
    console.log("Initializing app...");
    fetchDocuments();

    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            console.log("Send button clicked");
            sendChat();
        });
    }

    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendChat();
        });
    }
}

async function sendChat() {
    const input = document.getElementById('chatInput');
    if (!input.value.trim()) return;

    const messagesDiv = document.getElementById('messagesContainer');

    // Add user message
    addMessage(input.value, 'user');

    // Show loading
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message ai-message loading';
    loadingDiv.textContent = 'Thinking...';
    messagesDiv.appendChild(loadingDiv);

    const query = input.value;
    input.value = '';

    const apiKeyInput = document.getElementById('apiKey');
    const apiKey = apiKeyInput ? apiKeyInput.value : null;

    try {
        const payload = { query: query };
        if (apiKey) payload.api_key = apiKey;

        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();

        // Remove loading
        messagesDiv.removeChild(loadingDiv);

        // Add AI response
        addMessage(result.answer, 'ai');
    } catch (err) {
        if (messagesDiv.contains(loadingDiv)) {
            messagesDiv.removeChild(loadingDiv);
        }
        addMessage('Error getting response.', 'ai');
    }
}

function addMessage(text, sender) {
    const div = document.getElementById('messagesContainer');
    const msg = document.createElement('div');
    msg.className = `message ${sender}-message`;
    msg.textContent = text;
    msg.dir = "auto"; // Auto-detect LTR/RTL
    div.appendChild(msg);
    div.scrollTop = div.scrollHeight;
}
