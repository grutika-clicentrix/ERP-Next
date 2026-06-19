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
        var html = '<div class="table-responsive"><table>';
        rows.forEach(function(row, i) {
          var cells = row.split('|').filter(function(c) { return c.trim(); });
          if (i === 1 && cells.every(function(c) { return /^[-: ]+$/.test(c); })) return;
          var tag = (i === 0) ? 'th' : 'td';
          html += '<tr>' + cells.map(function(c) {
            return '<' + tag + '>' + c.trim() + '</' + tag + '>';
          }).join('') + '</tr>';
        });
        return html + '</table></div>';
      })
      .replace(/\n/g, '<br>');
  }

  function scrollToBottom() {
    if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function appendMessage(role, content, tokens) {
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
      
      if (tokens && typeof tokens === 'object' && tokens.total > 0) {
        var tokenBadge = document.createElement('div');
        tokenBadge.className = 'token-badge';
        tokenBadge.innerHTML = '✦ ' + tokens.total + ' tokens (' + tokens.prompt + ' prompt / ' + tokens.response + ' response)';
        bubble.appendChild(tokenBadge);
      }
      
      // Add Copy Button
      var copyBtn = document.createElement('button');
      copyBtn.className = 'copy-btn';
      copyBtn.title = 'Copy response';
      copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
      copyBtn.onclick = function() {
        navigator.clipboard.writeText(content);
        copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
        setTimeout(() => {
          copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
        }, 2000);
      };
      bubble.appendChild(copyBtn);
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
    
    // recreate welcome area with animation reset
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
          if (typeof r.message === 'object') {
             if (r.message.error) {
               appendMessage('ai', '⚠ ' + r.message.error);
             } else if (r.message.requires_approval) {
               renderApprovalCard(r.message.tool_call);
             } else if (r.message.reply !== undefined) {
               appendMessage('ai', r.message.reply, r.message.tokens);
               history.push({ role: 'assistant', content: r.message.reply });
             }
          } else {
             var reply = r.message;
             appendMessage('ai', reply);
             history.push({ role: 'assistant', content: reply });
          }
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

  window.sendApprovedAction = function(btn, name, argsStr) {
    var card = btn.closest('.approval-card');
    card.innerHTML = '<em>Action approved. Executing...</em>';
    
    var args = JSON.parse(decodeURIComponent(argsStr));
    var tool_call = {name: name, args: args};
    
    isLoading = true;
    showTyping();
    
    frappe.call({
      method: 'custom_ui.custom_ui.api.chat',
      args: {
        messages: JSON.stringify(history),
        approved_action: JSON.stringify(tool_call)
      },
      callback: function(r) {
        hideTyping();
        isLoading = false;
        if (r && r.message) {
          if (typeof r.message === 'object') {
             if (r.message.error) {
               appendMessage('ai', '⚠ ' + r.message.error);
             } else if (r.message.requires_approval) {
               renderApprovalCard(r.message.tool_call);
             } else if (r.message.reply !== undefined) {
               appendMessage('ai', r.message.reply, r.message.tokens);
               history.push({ role: 'assistant', content: r.message.reply });
             }
          } else {
             var reply = r.message;
             appendMessage('ai', reply);
             history.push({ role: 'assistant', content: reply });
          }
        }
      },
      error: function(err) {
        hideTyping();
        isLoading = false;
        appendMessage('ai', '⚠ Execution failed.');
      }
    });
  };

  window.rejectAction = function(btn) {
    var card = btn.closest('.approval-card');
    card.innerHTML = '<em style="color:#DC2626;">Action rejected by user.</em>';
    
    var rejectionMsg = 'I have rejected this action. Please abort and wait for my next instruction.';
    appendMessage('user', rejectionMsg);
    history.push({ role: 'user', content: rejectionMsg });
    
    isLoading = true;
    showTyping();
    frappe.call({
      method: 'custom_ui.custom_ui.api.chat',
      args: {
        messages: JSON.stringify(history)
      },
      callback: function(r) {
        hideTyping();
        isLoading = false;
        if (r && r.message) {
          if (typeof r.message === 'object') {
             if (r.message.error) {
               appendMessage('ai', '⚠ ' + r.message.error);
             } else if (r.message.requires_approval) {
               renderApprovalCard(r.message.tool_call);
             } else if (r.message.reply !== undefined) {
               appendMessage('ai', r.message.reply, r.message.tokens);
               history.push({ role: 'assistant', content: r.message.reply });
             }
          } else {
             var reply = r.message;
             appendMessage('ai', reply);
             history.push({ role: 'assistant', content: reply });
          }
        }
      }
    });
  };

  function renderApprovalCard(tool_call) {
    if (welcomeEl) welcomeEl.style.display = 'none';

    var row = document.createElement('div');
    row.className = 'msg-row ai';

    var avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = '✦';

    var bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    
    var argsStr = encodeURIComponent(JSON.stringify(tool_call.args || {})).replace(/'/g, "%27");
    var actionName = "Action Required";
    var userFriendlyMsg = "I need your permission to perform this action.";

    if (tool_call.name === "create_document") {
        actionName = "Create Record";
        userFriendlyMsg = "Can I create a new <strong>" + (tool_call.args.doctype || "record") + "</strong>?";
    } else if (tool_call.name === "update_document") {
        actionName = "Modify Record";
        userFriendlyMsg = "Can I modify the <strong>" + (tool_call.args.doctype || "record") + "</strong> (" + (tool_call.args.name || "Unknown") + ")?";
    } else if (tool_call.name === "execute_sql_query") {
        actionName = "Access Data";
        var dt = tool_call.args.target_doctype || "database";
        userFriendlyMsg = "Can I securely access the <strong>" + dt + "</strong> data to fulfill your request?";
    } else if (tool_call.name === "execute_document_method") {
        actionName = "Execute Workflow";
        var dt = tool_call.args.doctype || "record";
        var name = tool_call.args.name || "Unknown";
        var method = tool_call.args.method || "action";
        userFriendlyMsg = "Can I execute the method <strong>" + method + "</strong> on the <strong>" + dt + "</strong> (" + name + ")?";
    }

    bubble.innerHTML = `
        <div class="approval-card">
            <div class="approval-card-title">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                ${actionName}
            </div>
            <div class="approval-card-body" style="font-size: 14px; margin: 8px 0; color: var(--pro-text-main);">
                ${userFriendlyMsg}
            </div>
            <div class="approval-card-actions">
                <button class="approval-btn approve" onclick="sendApprovedAction(this, '${tool_call.name}', '${argsStr}')">Allow</button>
                <button class="approval-btn reject" onclick="rejectAction(this)">Deny</button>
            </div>
        </div>
    `;

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesEl.appendChild(row);
    scrollToBottom();
  }

  // Focus input
  setTimeout(function() { inputEl.focus(); }, 300);
};
