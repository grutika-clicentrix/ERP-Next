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
        <div class="avatar">✦</div>
        <div class="info">
          <div class="name">AI Assistant</div>
          <div class="status">Connected to ERPNext</div>
        </div>
        <button class="clear-btn" onclick="clearChat()">Clear chat</button>
      </div>

      <!-- Messages -->
      <div id="chat-messages">
        <div id="chat-welcome">
          <div class="icon">✦</div>
          <h3>What can I help you with?</h3>
          <p>Ask me anything about your ERPNext data — invoices, stock, sales orders, reports, and more.</p>
          <div class="suggestions">
            <div class="suggestion-chip" onclick="sendSuggestion(this)">Show overdue invoices</div>
            <div class="suggestion-chip" onclick="sendSuggestion(this)">What's our stock level for today?</div>
            <div class="suggestion-chip" onclick="sendSuggestion(this)">List pending purchase orders</div>
            <div class="suggestion-chip" onclick="sendSuggestion(this)">Top 5 customers this month</div>
            <div class="suggestion-chip" onclick="sendSuggestion(this)">Create a new Sales Order</div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div id="chat-input-area">
        <div id="chat-input-wrap">
          <textarea
            id="chat-input"
            placeholder="Ask about invoices, orders, stock, or any ERPNext data…"
            rows="1"
            onkeydown="handleKey(event)"
            oninput="autoResize(this)"
          ></textarea>
          <button id="send-btn" onclick="sendMessage()" title="Send">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"/>
            </svg>
          </button>
        </div>
        <div class="input-hint">Enter to send · Shift+Enter for new line</div>
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
      .replace(/`([^`]+)`/g, '<code style="background:#f1f5f9;padding:1px 5px;border-radius:4px;font-size:12px;font-family:monospace">$1</code>')
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
    if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function appendMessage(role, content) {
    if (welcomeEl) welcomeEl.style.display = 'none';

    var row = document.createElement('div');
    row.className = 'msg-row ' + role;

    var avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = role === 'user' ? '👤' : '✦';

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
    avatar.textContent = '✦';

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
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  };

  window.sendSuggestion = function(chip) {
    inputEl.value = chip.textContent;
    sendMessage();
  };

  window.clearChat = function() {
    history = [];
    messagesEl.innerHTML = '';
    
    // recreate welcome area
    var welcome = document.createElement('div');
    welcome.id = 'chat-welcome';
    welcome.innerHTML = `
      <div class="icon">✦</div>
      <h3>What can I help you with?</h3>
      <p>Ask me anything about your ERPNext data — invoices, stock, sales orders, reports, and more.</p>
      <div class="suggestions">
        <div class="suggestion-chip" onclick="sendSuggestion(this)">Show overdue invoices</div>
        <div class="suggestion-chip" onclick="sendSuggestion(this)">What's our stock level for today?</div>
        <div class="suggestion-chip" onclick="sendSuggestion(this)">List pending purchase orders</div>
        <div class="suggestion-chip" onclick="sendSuggestion(this)">Top 5 customers this month</div>
        <div class="suggestion-chip" onclick="sendSuggestion(this)">Create a new Sales Order</div>
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
