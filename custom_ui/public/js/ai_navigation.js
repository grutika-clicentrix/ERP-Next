frappe.provide("custom_ui");

$(document).ready(function() {
    function injectAINav() {
        const sidebar = $(".body-sidebar, .desk-sidebar");
        if (sidebar.length === 0) return;
        
        if ($("#ai-sidebar-nav").length > 0) return;

        let aiNavHtml = `
            <div class="sidebar-item-container" id="ai-sidebar-nav" style="margin-bottom: 8px;">
                <div class="standard-sidebar-item">
                    <a href="/app/ai" class="item-anchor" style="display: flex; align-items: center; gap: 10px; padding: 7px 10px; text-decoration: none;">
                        <span class="sidebar-item-icon" style="color: #0099A3; font-size: 16px; display: flex; align-items: center; justify-content: center; width: 20px;">⚼</span>
                        <span class="sidebar-item-label" style="font-weight: 600;">AI Assistant</span>
                    </a>
                </div>
            </div>
        `;
        
        let firstItem = sidebar.find(".sidebar-item-container").first();
        if (firstItem.length > 0) {
            firstItem.before(aiNavHtml);
        } else {
            sidebar.prepend(aiNavHtml);
        }

        updateActiveState();
    }

    function updateActiveState() {
        $("#ai-sidebar-nav").removeClass("active selected");
        if (frappe.get_route && frappe.get_route()[0] === "ai") {
            $("#ai-sidebar-nav").addClass("selected active");
        }
    }

    setInterval(injectAINav, 1000);

    if (frappe.router) {
        frappe.router.on("change", function() {
            setTimeout(injectAINav, 50);
            updateActiveState();
        });
    }
    document.addEventListener("page-change", function() {
        setTimeout(injectAINav, 50);
        updateActiveState();
    });
});