frappe.pages["ai"].on_page_load = function (wrapper) {
  console.log("AI Assistant page loaded!");

  let page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "AI Assistant",
    single_column: true,
  });

  // Inline HTML markup directly to bypass template cache issues
  let html = `
    <div id="ai-chat-root">
      <!-- Header -->
      <div id="chat-header">
        <div class="avatar">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a10 10 0 1 0 10 10H12V2z"></path>
            <path d="M12 12L2.1 14.8a10 10 0 0 1 9.9-12.8V12z"></path>
          </svg>
        </div>
        <div class="info">
          <div class="name">AI Copilot</div>
          <div class="status">System Active & Connected</div>
        </div>
        <button class="clear-btn" onclick="clearChat()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px; vertical-align: middle;">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
          Clear
        </button>
      </div>

      <!-- Messages -->
      <div id="chat-messages">
        <div id="chat-welcome">
          <div class="icon-wrapper">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
              <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
              <line x1="12" y1="22.08" x2="12" y2="12"></line>
            </svg>
          </div>
          <h3>How can I help you today?</h3>
          <p>Your intelligent assistant for ERPNext. Ask about invoices, inventory, sales orders, or generate comprehensive reports.</p>
          <div class="suggestions">
            <div class="suggestion-chip" style="animation-delay: 0.1s" onclick="sendSuggestion(this)">📦 Show low stock items</div>
            <div class="suggestion-chip" style="animation-delay: 0.2s" onclick="sendSuggestion(this)">📄 List pending purchase orders</div>
            <div class="suggestion-chip" style="animation-delay: 0.3s" onclick="sendSuggestion(this)">📈 Top 5 customers this month</div>
            <div class="suggestion-chip" style="animation-delay: 0.4s" onclick="sendSuggestion(this)">➕ Create a new Sales Order</div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div id="chat-input-area">
        <div id="chat-input-wrap">
          <textarea
            id="chat-input"
            placeholder="Ask anything about your data..."
            rows="1"
            onkeydown="handleKey(event)"
            oninput="autoResize(this)"
          ></textarea>
          <button id="send-btn" onclick="sendMessage()" title="Send">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
        <div class="input-hint">Press <strong>Enter</strong> to send · <strong>Shift+Enter</strong> for a new line</div>
      </div>
    </div>
  `;

  // Render HTML template into the page body
  page.main.html(html);

  // State
  var history = [];
  var isLoading = false;

  // DOM elements (scoped to this page wrapper)
  var messagesEl = wrapper.querySelector('#chat-messages');
  var inputEl    = wrapper.querySelector('#chat-input');
  var sendBtn    = wrapper.querySelector('#send-btn');
  var welcomeEl  = wrapper.querySelector('#chat-welcome');

  function renderMarkdown(text) {
    return text
      .replace(/\*\*(.*?)\*\//g, '<strong>$1</strong>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code style="background:#f1f5f9;padding:2px 6px;border-radius:6px;font-size:13px;font-family:monospace;color:#1E293B;border:1px solid #E2E8F0">$1</code>')
      .replace(/((?:\|.+\|\n?)+)/g, function(match) {
        var rows = match.trim().split('\n').filter(function(r) { return r.trim(); });
        var html = '<table>';
        rows.forEach(function(row, i) {
          var cells = row.split('|').filter(function(c) { return c.trim(); });
          if (i === 1 && cells.every(function(c) { return /^[-: ]+$/.test(c); })) return;
          var tag = (i === 0) ? 'th' : 'td';
          html += '<tr>' + cells.map(function(c) {
            return '<' + tag + '>' + c.trim() + '</' + tag + '>';
          }).join('') + '</tr>';
        });
        return html + '</table>';
      })
      .replace(/\n/g, '<br>');
  }

  function scrollToBottom() {
    if (messagesEl) {
      setTimeout(() => {
        messagesEl.scrollTop = messagesEl.scrollHeight;
      }, 50); // slight delay to allow rendering
    }
  }

  function appendMessage(role, content) {
    if (welcomeEl) welcomeEl.style.display = 'none';

    var row = document.createElement('div');
    row.className = 'msg-row ' + role;

    var avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    
    if (role === 'user') {
      avatar.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
          <circle cx="12" cy="7" r="4"></circle>
        </svg>
      `;
    } else {
      avatar.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a10 10 0 1 0 10 10H12V2z"></path>
          <path d="M12 12L2.1 14.8a10 10 0 0 1 9.9-12.8V12z"></path>
        </svg>
      `;
    }

    var bubble = document.createElement('div');
    bubble.className = 'msg-bubble';

    if (role === 'user') {
      bubble.textContent = content;
    } else {
      bubble.innerHTML = renderMarkdown(content);
    }

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesEl.appendChild(row);
    scrollToBottom();
  }

  function showTyping() {
    var row = document.createElement('div');
    row.className = 'msg-row ai';
    row.id = 'typing-row';

    var avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2a10 10 0 1 0 10 10H12V2z"></path>
        <path d="M12 12L2.1 14.8a10 10 0 0 1 9.9-12.8V12z"></path>
      </svg>
    `;

    var indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = '<span></span><span></span><span></span>';

    row.appendChild(avatar);
    row.appendChild(indicator);
    messagesEl.appendChild(row);
    scrollToBottom();
  }

  // Bind handlers globally on window (mapped to current active wrapper scope)
  window.handleKey = function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  window.autoResize = function(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 150) + 'px';
  };

  window.sendSuggestion = function(chip) {
    // Strip the emoji prefix for the actual query if present
    let text = chip.textContent;
    if (text.match(/^[^\w\s]/)) {
      text = text.substring(2).trim();
    }
    inputEl.value = text;
    sendMessage();
  };

  window.clearChat = function() {
    history = [];
    messagesEl.innerHTML = '';
    
    // recreate welcome area
    var welcome = document.createElement('div');
    welcome.id = 'chat-welcome';
    welcome.innerHTML = `
      <div class="icon-wrapper">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
          <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
          <line x1="12" y1="22.08" x2="12" y2="12"></line>
        </svg>
      </div>
      <h3>How can I help you today?</h3>
      <p>Your intelligent assistant for ERPNext. Ask about invoices, inventory, sales orders, or generate comprehensive reports.</p>
      <div class="suggestions">
        <div class="suggestion-chip" style="animation-delay: 0.1s" onclick="sendSuggestion(this)">📦 Show low stock items</div>
        <div class="suggestion-chip" style="animation-delay: 0.2s" onclick="sendSuggestion(this)">📄 List pending purchase orders</div>
        <div class="suggestion-chip" style="animation-delay: 0.3s" onclick="sendSuggestion(this)">📈 Top 5 customers this month</div>
        <div class="suggestion-chip" style="animation-delay: 0.4s" onclick="sendSuggestion(this)">➕ Create a new Sales Order</div>
      </div>
    `;
    messagesEl.appendChild(welcome);
    welcomeEl = welcome;
  };

  function hideTyping() {
    var el = wrapper.querySelector('#typing-row');
    if (el) el.remove();
  }

  function sendMessage() {
    var text = inputEl.value.trim();
    if (!text || isLoading) return;

    inputEl.value = '';
    inputEl.style.height = 'auto';
    isLoading = true;
    sendBtn.disabled = true;

    appendMessage('user', text);
    history.push({ role: 'user', content: text });
    showTyping();

    frappe.call({
      method: 'custom_ui.custom_ui.api.chat',
      args: {
        messages: JSON.stringify(history)
      },
      callback: function(r) {
        hideTyping();
        isLoading = false;
        sendBtn.disabled = false;

        if (r && r.message) {
          var reply = r.message;
          appendMessage('ai', reply);
          history.push({ role: 'assistant', content: reply });
        } else {
          appendMessage('ai', '⚠ Sorry, I could not get a response. Please try again.');
        }
      },
      error: function(err) {
        hideTyping();
        isLoading = false;
        sendBtn.disabled = false;
        appendMessage('ai', '⚠ Connection error. Verify your Gemini API key is configured.');
        console.error('AI chat error:', err);
      }
    });
  }

  window.sendMessage = sendMessage;

  // Focus input
  setTimeout(function() { inputEl.focus(); }, 300);
};
