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
                    <span class="sidebar-item-icon" style="color: #10B981; font-size: 16px; display: flex; align-items: center; justify-content: center; width: 20px;">✦</span>
                    <span class="sidebar-item-label" style="font-weight: 600;">AI Assistant</span>
                </a>
            </div>
        `;
        
        // Find the "Modules" section or the first standard section and prepend to it
        let targetSection = $('.desk-sidebar .standard-sidebar-section').first();
        if (targetSection.length > 0) {
            let ul = targetSection.find('.sidebar-items');
            if (ul.length > 0) {
                ul.prepend(aiNavHtml);
            } else {
                targetSection.prepend(aiNavHtml);
            }
        } else {
            // Fallback for custom desk setups
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

    // Run on init with slight delay to ensure sidebar is rendered
    setTimeout(injectAINav, 1500);

    // Run on route change
    if (frappe.router) {
        frappe.router.on('change', function() {
            setTimeout(injectAINav, 300);
            updateActiveState();
        });
    }
});
