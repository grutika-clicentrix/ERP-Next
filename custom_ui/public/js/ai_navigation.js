frappe.provide("custom_ui");

$(document).ready(function() {
    // Inject the AI Assistant navigation to the global Frappe sidebar
    function injectAINav() {
        if ($('.desk-sidebar').length === 0) return;
        
        // Prevent duplicate injection
        if ($('#ai-sidebar-nav').length > 0) return;

        let aiNavHtml = `
            <div class="sidebar-item-container" id="ai-sidebar-nav" style="margin-bottom: 8px;">
                <a href="/app/ai" class="sidebar-item desk-sidebar-item" style="display: flex; align-items: center; gap: 10px; padding: 6px 8px; text-decoration: none;">
                    <span class="sidebar-item-icon" style="color: #0099A3; font-size: 16px; display: flex; align-items: center; justify-content: center; width: 20px;">✦</span>
                    <span class="sidebar-item-label" style="font-weight: 600;">AI Assistant</span>
                </a>
            </div>
        `;
        
        // Try to find the exact container holding the sidebar items (works with Vue in Frappe v14/v15)
        let firstItem = $('.desk-sidebar .sidebar-item-container').first();
        if (firstItem.length > 0) {
            firstItem.before(aiNavHtml);
        } else {
            // Fallback
            $('.desk-sidebar').prepend(aiNavHtml);
        }

        updateActiveState();
    }

    function updateActiveState() {
        $('#ai-sidebar-nav').removeClass('active');
        if (frappe.get_route && frappe.get_route()[0] === 'ai') {
            $('#ai-sidebar-nav').addClass('active');
        }
    }

    // Frappe v14/v15 uses Vue to render the sidebar dynamically. 
    // It can wipe out jQuery injections when the route changes or data loads.
    // An interval ensures our custom item is always placed back if missing.
    setInterval(injectAINav, 1000);

    // Run immediately on route change to prevent flicker
    if (frappe.router) {
        frappe.router.on('change', function() {
            setTimeout(injectAINav, 50);
            updateActiveState();
        });
    }
});
