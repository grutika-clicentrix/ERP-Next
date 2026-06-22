frappe.pages["ai"].on_page_load = function (wrapper) {
  console.log("AI Assistant page loaded!");

  // Add custom class to target wrappers for layout overrides
  $(wrapper).addClass('ai-assistant-page-wrapper');
  $('body').addClass('ai-assistant-page-active');

  frappe.pages["ai"].on_page_show = function (wrapper) {
    $('body').addClass('ai-assistant-page-active');
    // scroll to bottom on load
    if (typeof scrollToBottom === 'function') {
      scrollToBottom();
    }
  };

  frappe.pages["ai"].on_page_hide = function (wrapper) {
    $('body').removeClass('ai-assistant-page-active');
  };

  let page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "AI Assistant",
    single_column: true,
  });
  const ALL_PROMPTS = [
    { text: "Show today's revenue vs target and cash position.", icon: "💰" },
    { text: "Show yesterday's production output and downtime.", icon: "🏭" },
    { text: "Show our on-time delivery rate this week.", icon: "📦" },
    { text: "What approvals are pending in my queue?", icon: "✅" },
    { text: "Show the sales pipeline and order book status.", icon: "📊" },
    { text: "Show capacity utilization across all plants.", icon: "⚙️" },
    { text: "Show current cash position across all bank accounts.", icon: "🏦" },
    { text: "List clients with invoices overdue by more than 30 days.", icon: "🧾" },
    { text: "Which product lines have the lowest gross margins?", icon: "📉" },
    { text: "Compare actual operational expenses vs budget.", icon: "📋" },
    { text: "Show P&L and Cash Flow summary for today.", icon: "📈" },
    { text: "List all tax and compliance deadlines this month.", icon: "📅" },
    { text: "Are there any supplier delays affecting production today?", icon: "🚛" },
    { text: "Check raw material levels across all warehouses.", icon: "📦" },
    { text: "Where are the bottlenecks in order fulfillment?", icon: "🔍" },
    { text: "Show scheduled production capacity for tomorrow.", icon: "🗓️" },
    { text: "Show net profit margin trend for this week.", icon: "💹" },
    { text: "List operational issues not resolved today.", icon: "⚠️" },
    { text: "Compare shipping costs of our top 3 delivery partners.", icon: "🚢" },
    { text: "Give me a 5-minute briefing on company performance today.", icon: "⚡" },
  ];

  let tickerInterval = null;
  let tickerIndex = 0;

  function formatPromptTextForDisplay(text) {
    return text.replace(/\[([^\]]+)\]/g, function (match, placeholder) {
      return '<span class="prompt-text-placeholder">[' + placeholder + ']</span>';
    });
  }

  function stopTicker() {
    if (tickerInterval) {
      clearInterval(tickerInterval);
      tickerInterval = null;
    }
  }

  function startTicker() {
    stopTicker();
    tickerIndex = 0;
    renderTickerSlide(true);
    tickerInterval = setInterval(function () {
      tickerIndex = (tickerIndex + 2) % ALL_PROMPTS.length;
      renderTickerSlide(false);
    }, 3800);
  }

  function renderTickerSlide(instant) {
    const track = wrapper.querySelector('#prompt-ticker-track');
    if (!track) return;

    const idx1 = tickerIndex % ALL_PROMPTS.length;
    const idx2 = (tickerIndex + 1) % ALL_PROMPTS.length;

    const makeCard = (p) => {
      const displayHtml = formatPromptTextForDisplay(p.text);
      return `<div class="ticker-prompt-card" data-prompt="${p.text.replace(/"/g, '&quot;')}">
        <div class="ticker-card-icon">${p.icon}</div>
        <div class="ticker-prompt-text">${displayHtml}</div>
        <div class="ticker-prompt-arrow">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
        </div>
      </div>`;
    };

    const attachClicks = () => {
      track.querySelectorAll('.ticker-prompt-card').forEach(card => {
        card.addEventListener('click', () => {
          const pt = card.getAttribute('data-prompt');
          if (typeof window.selectSuggestion === 'function') window.selectSuggestion(pt);
        });
      });
    };

    if (instant) {
      track.innerHTML = makeCard(ALL_PROMPTS[idx1]) + makeCard(ALL_PROMPTS[idx2]);
      attachClicks();
    } else {
      track.style.transition = 'none';
      track.style.opacity = '0';
      track.style.transform = 'translateY(10px)';
      setTimeout(() => {
        track.innerHTML = makeCard(ALL_PROMPTS[idx1]) + makeCard(ALL_PROMPTS[idx2]);
        attachClicks();
        track.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        track.style.opacity = '1';
        track.style.transform = 'translateY(0)';
      }, 90);
    }
  }

  function initExecutiveSuite() {
    const root = wrapper.querySelector('#executive-suite-root');
    if (!root) return;

    root.innerHTML = `
      <div class="executive-suite-container">
        <div class="prompt-ticker-wrapper">
          <div class="prompt-ticker-track" id="prompt-ticker-track"></div>
        </div>
      </div>
    `;

    startTicker();
  }




  // Inline HTML markup directly to bypass template cache issues
  let html = `
    <div id="ai-chat-root">
      <!-- Header -->
      <div id="chat-header">
        <div class="avatar">✦</div>
        <div class="info">
          <div class="name">AI Assistant</div>
        </div>
        <button class="clear-btn" onclick="clearChat()">Clear chat</button>
      </div>

      <!-- Messages -->
      <div id="chat-messages">
        <div id="chat-welcome">
          <div class="welcome-hero">
            <div class="welcome-icon-ring">
              <div class="welcome-icon-glow"></div>
              <div class="welcome-icon">✦</div>
            </div>
            <h2 class="welcome-headline">
              Your Business,<br>
              <span class="welcome-headline-accent">Instantly Understood</span>
            </h2>
            <p class="welcome-sub">Ask about <span class="welcome-kw">revenue</span>, <span class="welcome-kw">inventory</span>, <span class="welcome-kw">orders</span>, <span class="welcome-kw">cash flow</span> — get instant answers from your live ERP data.</p>
          </div>
          <div id="executive-suite-root"></div>
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

  // Initialize dynamic prompt suggestion component
  initExecutiveSuite();

  // State
  var history = [];
  var isLoading = false;

  // DOM elements (scoped to this page wrapper)
  var messagesEl = wrapper.querySelector('#chat-messages');
  var inputEl = wrapper.querySelector('#chat-input');
  var sendBtn = wrapper.querySelector('#send-btn');
  var welcomeEl = wrapper.querySelector('#chat-welcome');

  function renderMarkdown(text) {
    if (!text) return "";

    // 1. Escape HTML to prevent malicious code injection
    var escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // 2. Preformatted Code blocks (```code```)
    escaped = escaped.replace(/```([\s\S]*?)```/g, function (match, code) {
      var trimmed = code.trim();
      if (trimmed.startsWith('chart\n') || trimmed.startsWith('chart\r\n')) {
        var jsonStr = trimmed.substring(5).trim();
        // Undo HTML escaping for JSON content
        jsonStr = jsonStr.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
        var encodedConfig = encodeURIComponent(jsonStr);
        return '<div class="ai-chart-container" style="width: 100%; min-height: 250px; margin: 15px 0; background: var(--bg-color, #fff); border-radius: 8px; padding: 10px; border: 1px solid var(--border-color, #e2e8f0);" data-chart-config="' + encodedConfig + '"></div>';
      }
      return '<pre><code>' + code.trim() + '</code></pre>';
    });

    // 3. Inline code (`code`)
    escaped = escaped.replace(/`([^`\n]+)`/g, '<code>$1</code>');

    // 4. Bold formatting (**text**)
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // 5. Render markdown tables
    escaped = escaped.replace(/((?:\|[^\n]+\|\n?)+)/g, function (match) {
      var rows = match.trim().split('\n').filter(function (r) { return r.trim(); });
      var html = '<div class="table-responsive"><table>';
      rows.forEach(function (row, i) {
        var cells = row.split('|').map(function (c) { return c.trim(); });

        // Remove empty edge cells from markdown table syntax
        if (cells[0] === '') cells.shift();
        if (cells[cells.length - 1] === '') cells.pop();

        if (i === 1 && cells.every(function (c) { return /^[-: ]+$/.test(c); })) return;
        var tag = (i === 0) ? 'th' : 'td';
        html += '<tr>' + cells.map(function (c) {
          return '<' + tag + '>' + c + '</' + tag + '>';
        }).join('') + '</tr>';
      });
      return html + '</table></div>';
    });

    // 6. Handle newlines outside of pre codeblocks
    var parts = escaped.split(/(<\/pre>|<pre>|<div class="ai-chart-container"|<\/div>)/g);
    var insidePreOrChart = false;
    for (var j = 0; j < parts.length; j++) {
      if (parts[j] === '<pre>' || parts[j] === '<div class="ai-chart-container"') {
        insidePreOrChart = true;
      } else if (parts[j] === '</pre>' || (insidePreOrChart && parts[j] === '</div>')) {
        insidePreOrChart = false;
      } else if (!insidePreOrChart) {
        parts[j] = parts[j].replace(/\n/g, '<br>');
      }
    }
    return parts.join('');
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

      // Initialize charts
      var charts = bubble.querySelectorAll('.ai-chart-container');
      charts.forEach(function (container) {
        try {
          var configStr = decodeURIComponent(container.getAttribute('data-chart-config'));
          var config = JSON.parse(configStr);

          // Render using Frappe Charts
          new frappe.Chart(container, config);
        } catch (e) {
          console.error("Failed to render chart", e);
          container.innerHTML = '<div style="color:var(--text-color, red); padding: 10px; font-size: 13px;">⚠ Failed to render chart: ' + e.message + '</div>';
        }
      });

      // Add Copy Button
      var copyBtn = document.createElement('button');
      copyBtn.className = 'copy-btn';
      copyBtn.title = 'Copy response';
      copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
      copyBtn.onclick = function () {
        navigator.clipboard.writeText(content);
        copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="#0099A3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
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

  // Bind handlers globally on window (mapped to wrapper scope)
  window.handleKey = function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  window.autoResize = function (el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  };

  window.selectSuggestion = function (text) {
    inputEl.value = text;
    autoResize(inputEl);
    inputEl.focus();

    // Auto-highlight the first placeholder bracket [Placeholder] if present
    var start = text.indexOf('[');
    if (start !== -1) {
      var end = text.indexOf(']', start);
      if (end !== -1) {
        // Use setTimeout to ensure selection is executed after browser focuses inputEl
        setTimeout(function () {
          inputEl.setSelectionRange(start, end + 1);
        }, 50);
      }
    }
  };

  window.clearChat = function () {
    history = [];
    messagesEl.innerHTML = '';

    // recreate welcome area with animation reset
    var welcome = document.createElement('div');
    welcome.id = 'chat-welcome';
    welcome.innerHTML = `
      <div class="icon">✦</div>
      <h3>What can I help you with?</h3>
      <p>Ask me anything about your ERPNext data — invoices, stock, sales orders, reports, and more.</p>
      <div id="executive-suite-root"></div>
    `;
    messagesEl.appendChild(welcome);
    welcomeEl = welcome;

    initExecutiveSuite();
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
      callback: function (r) {
        hideTyping();
        isLoading = false;
        sendBtn.disabled = false;

        if (r && r.message) {
          if (typeof r.message === 'object') {
            if (r.message.new_history) {
              r.message.new_history.forEach(function (msg) {
                history.push(msg);
              });
            }
            if (r.message.error) {
              appendMessage('ai', '⚠ ' + r.message.error);
            } else if (r.message.requires_approval) {
              renderApprovalCard(r.message.tool_call);
            } else if (r.message.reply !== undefined) {
              appendMessage('ai', r.message.reply);
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
      error: function (err) {
        hideTyping();
        isLoading = false;
        sendBtn.disabled = false;
        appendMessage('ai', '⚠ Connection error. Verify your Gemini API key is configured.');
        console.error('AI chat error:', err);
      }
    });
  }

  window.sendMessage = sendMessage;

  window.sendApprovedAction = function (btn, name, argsStr) {
    var card = btn.closest('.approval-card');
    card.innerHTML = '<em style="color: var(--pro-primary); font-weight: 500;">Action approved. Executing...</em>';

    var args = JSON.parse(decodeURIComponent(argsStr));
    var tool_call = { name: name, args: args };

    isLoading = true;
    showTyping();

    frappe.call({
      method: 'custom_ui.custom_ui.api.chat',
      args: {
        messages: JSON.stringify(history),
        approved_action: JSON.stringify(tool_call)
      },
      callback: function (r) {
        hideTyping();
        isLoading = false;
        if (r && r.message) {
          if (typeof r.message === 'object') {
            if (r.message.new_history) {
              r.message.new_history.forEach(function (msg) {
                history.push(msg);
              });
            }
            if (r.message.error) {
              appendMessage('ai', '⚠ ' + r.message.error);
            } else if (r.message.requires_approval) {
              renderApprovalCard(r.message.tool_call);
            } else if (r.message.reply !== undefined) {
              appendMessage('ai', r.message.reply);
              history.push({ role: 'assistant', content: r.message.reply });
            }
          } else {
            var reply = r.message;
            appendMessage('ai', reply);
            history.push({ role: 'assistant', content: reply });
          }
        }
      },
      error: function (err) {
        hideTyping();
        isLoading = false;
        appendMessage('ai', '⚠ Execution failed.');
      }
    });
  };

  window.rejectAction = function (btn) {
    var card = btn.closest('.approval-card');
    card.innerHTML = '<em style="color:#E11D48; font-weight: 500;">Action rejected by user.</em>';

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
      callback: function (r) {
        hideTyping();
        isLoading = false;
        if (r && r.message) {
          if (typeof r.message === 'object') {
            if (r.message.new_history) {
              r.message.new_history.forEach(function (msg) {
                history.push(msg);
              });
            }
            if (r.message.error) {
              appendMessage('ai', '⚠ ' + r.message.error);
            } else if (r.message.requires_approval) {
              renderApprovalCard(r.message.tool_call);
            } else if (r.message.reply !== undefined) {
              appendMessage('ai', r.message.reply);
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

  // Toggle technical details disclosure panel
  window.toggleDetails = function (id) {
    var content = wrapper.querySelector('#' + id);
    var toggleBtn = content.previousElementSibling;
    if (content.classList.contains('open')) {
      content.classList.remove('open');
      toggleBtn.classList.remove('open');
      toggleBtn.querySelector('svg').style.transform = 'rotate(0deg)';
    } else {
      content.classList.add('open');
      toggleBtn.classList.add('open');
      toggleBtn.querySelector('svg').style.transform = 'rotate(90deg)';
    }
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
      actionName = "Create Document";
      userFriendlyMsg = "Create a new <strong>" + (tool_call.args.doctype || "document") + "</strong>?";
    } else if (tool_call.name === "update_document") {
      actionName = "Update Document";
      userFriendlyMsg = "Update the <strong>" + (tool_call.args.doctype || "document") + "</strong> (" + (tool_call.args.name || "Unknown") + ")?";
    } else if (tool_call.name === "execute_sql_query") {
      actionName = "Analyze Information";
      var dt = tool_call.args.target_doctype || "data";
      userFriendlyMsg = "Analyze and summarize the <strong>" + dt + "</strong> information?";
    } else if (tool_call.name === "execute_document_method") {
      actionName = "Process Workflow Step";
      var dt = tool_call.args.doctype || "document";
      var name = tool_call.args.name || "Unknown";
      var method = tool_call.args.method || "action";
      userFriendlyMsg = "Execute the action <strong>" + method + "</strong> on the <strong>" + dt + "</strong> (" + name + ")?";
    } else if (tool_call.name === "send_email") {
      actionName = "Send Notification";
      var rcpts = tool_call.args.recipients || "someone";
      var subj = tool_call.args.subject || "No Subject";
      userFriendlyMsg = "Send email to <strong>" + rcpts + "</strong> with subject <strong>" + subj + "</strong>?";
    }

    // Prepare tech details content
    var detailsHtml = "";
    if (tool_call.args && Object.keys(tool_call.args).length > 0) {
      var detailsContent = "";
      if (tool_call.name === "execute_sql_query" && tool_call.args.query) {
        detailsContent = tool_call.args.query;
      } else {
        detailsContent = JSON.stringify(tool_call.args, null, 2);
      }

      var toggleId = 'details-' + Math.random().toString(36).substr(2, 9);
      detailsHtml = `
        <button class="approval-details-toggle" onclick="toggleDetails('${toggleId}')">
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="transform: rotate(0deg);"><polyline points="9 18 15 12 9 6"></polyline></svg>
          Show data details
        </button>
        <div id="${toggleId}" class="approval-details-content">
          <pre>${detailsContent}</pre>
        </div>
      `;
    }

    bubble.innerHTML = `
        <div class="approval-card">
            <div class="approval-card-title">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                ${actionName}
            </div>
            <div class="approval-card-body">
                ${userFriendlyMsg}
                ${detailsHtml}
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
  setTimeout(function () { inputEl.focus(); }, 300);
};
