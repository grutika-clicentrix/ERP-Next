/**
 * theme_manager.js — Custom UI PRO
 * =================================
 * Dynamic Navbar Banner Theme Manager (Dynamics 365–inspired)
 *
 * Included via app_include_js. Responsibilities:
 *   1. Apply CSS variables from frappe.boot on page load (zero FOUC).
 *   2. Inject a "Personalize Navbar" item into the user avatar dropdown.
 *   3. Show a theme-selector Dialog with image thumbnail grid.
 *   4. Preview on click, persist on Save.
 */

(function () {
    "use strict";

    /* ─────────────────────────────────────────────
       CONSTANTS
    ───────────────────────────────────────────── */
    const CSS_VAR_BG   = "--dynamic-navbar-bg";
    const CSS_VAR_TEXT = "--dynamic-navbar-text";
    const MENU_ITEM_ID = "custom-ui-personalize-navbar-btn";

    /* ─────────────────────────────────────────────
       STEP 1 — Apply theme from boot (instant, no flash)
    ───────────────────────────────────────────── */
    function applyBootTheme() {
        const details = (frappe.boot && frappe.boot.user_theme_details) || null;
        if (details && details.bg_image) {
            setCSSVariables(details.bg_image, details.text_color || "#FFFFFF");
        }
    }

    /**
     * Inject CSS custom properties onto :root so every CSS rule that
     * references var(--dynamic-navbar-bg) picks up the new value instantly.
     *
     * @param {string} imageUrl   - Full URL (or Frappe /files/... path) of the image
     * @param {string} textColor  - Hex color for all navbar text/icons
     */
    function setCSSVariables(imageUrl, textColor) {
        const root = document.documentElement;
        if (imageUrl) {
            root.style.setProperty(CSS_VAR_BG, `url("${imageUrl}")`);
        } else {
            // Revert to solid fallback colour when clearing the theme
            root.style.setProperty(CSS_VAR_BG, "#203535");
        }
        root.style.setProperty(CSS_VAR_TEXT, textColor || "#FFFFFF");

        // Dynamically update the breadcrumb override injected by breadcrumb_chevron_fix.js
        updateBreadcrumbColor(textColor || "#FFFFFF");
    }

    /** Keep breadcrumb separator colour in sync with the dynamic text colour. */
    function updateBreadcrumbColor(color) {
        let dynStyle = document.getElementById("custom-ui-dynamic-breadcrumb");
        if (!dynStyle) {
            dynStyle = document.createElement("style");
            dynStyle.id = "custom-ui-dynamic-breadcrumb";
            document.head.appendChild(dynStyle);
        }
        dynStyle.textContent = `
            html body .navbar ul#navbar-breadcrumbs li + li::before,
            html body ul#navbar-breadcrumbs li + li::before,
            html body ul#navbar-breadcrumbs li::before,
            html body ul#navbar-breadcrumbs li::after {
                color: ${color} !important;
                opacity: 1 !important;
            }
            html body ul#navbar-breadcrumbs svg,
            html body ul#navbar-breadcrumbs .breadcrumb-separator svg {
                fill: ${color} !important;
                stroke: ${color} !important;
                color: ${color} !important;
            }
        `;
    }

    /* ─────────────────────────────────────────────
       STEP 2 — Inject "Personalize Navbar" menu item
    ───────────────────────────────────────────── */
    function injectMenuItems() {
        // Guard: only inject once and only when the dropdown exists
        if (document.getElementById(MENU_ITEM_ID)) return;

        const dropdownMenu = document.querySelector(
            ".navbar .dropdown-menu[data-toggle='dropdown'], " +
            ".navbar .navbar-right .dropdown-menu, " +
            ".navbar .user-menu .dropdown-menu, " +
            // Frappe v15 selector
            ".navbar .nav-item.dropdown .dropdown-menu"
        );

        if (!dropdownMenu) return;

        // Find an existing divider or the last item to insert before/after
        const divider = document.createElement("li");
        divider.className = "dropdown-divider";
        divider.setAttribute("role", "separator");

        const menuItem = document.createElement("li");
        menuItem.id   = MENU_ITEM_ID;
        menuItem.innerHTML = `
            <a class="dropdown-item" href="#" id="${MENU_ITEM_ID}-link"
               style="display:flex;align-items:center;gap:8px;padding:8px 20px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14"
                     viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                     style="flex-shrink:0;">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"></path>
                    <path d="M12 2v2M12 20v2M2 12h2M20 12h2"></path>
                </svg>
                <span>Personalize Navbar</span>
            </a>`;

        // Insert divider + item before the last divider/logout item
        const logoutDivider = dropdownMenu.querySelector(".dropdown-divider:last-of-type");
        if (logoutDivider) {
            dropdownMenu.insertBefore(menuItem, logoutDivider);
            dropdownMenu.insertBefore(divider, menuItem);
        } else {
            dropdownMenu.appendChild(divider);
            dropdownMenu.appendChild(menuItem);
        }

        document.getElementById(`${MENU_ITEM_ID}-link`).addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            // Close the dropdown first
            const toggleBtn = document.querySelector(".navbar .nav-item.dropdown .nav-link.dropdown-toggle");
            if (toggleBtn) toggleBtn.click();
            setTimeout(openThemeDialog, 150);
        });
    }

    /* ─────────────────────────────────────────────
       STEP 3 — Theme Selector Dialog
    ───────────────────────────────────────────── */
    let _selectedTheme = null; // tracks the currently previewed theme

    function openThemeDialog() {
        const dialog = new frappe.ui.Dialog({
            title: "🎨 Personalize Your Navbar",
            size: "large",
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "theme_grid_html",
                    options: `<div id="navbar-theme-grid-loader"
                                   style="display:flex;align-items:center;justify-content:center;
                                          min-height:180px;color:#6B7280;gap:10px;">
                                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"
                                       viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                       stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                                       class="spin-icon"
                                       style="animation:spin 1s linear infinite;">
                                      <path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0"/>
                                  </svg>
                                  Loading themes...
                              </div>
                              <div id="navbar-theme-grid" style="display:none;"></div>
                              <style>
                                  @keyframes spin { to { transform: rotate(360deg); } }
                              </style>`,
                },
            ],
            primary_action_label: "✅ Save Theme",
            primary_action(values) {
                if (!_selectedTheme) {
                    frappe.show_alert({ message: "Please select a theme first.", indicator: "orange" });
                    return;
                }
                saveTheme(_selectedTheme, dialog);
            },
            secondary_action_label: "↩️ Reset to Default",
            secondary_action() {
                _selectedTheme = { name: "", bg_image: "", text_color: "#FFFFFF", theme_name: "Default" };
                setCSSVariables("", "#FFFFFF");
                saveTheme(_selectedTheme, dialog);
            },
        });

        dialog.show();

        // Reset selection state each time dialog opens
        _selectedTheme = null;

        // Populate current selection from boot
        const currentTheme = (frappe.boot && frappe.boot.user_theme_details) || null;

        // Fetch all active themes
        frappe.db.get_list("Navbar Theme", {
            filters: { is_active: 1 },
            fields: ["name", "theme_name", "background_image_url", "navbar_text_color"],
            limit: 50,
        }).then(function (themes) {
            renderThemeGrid(themes, currentTheme);
        }).catch(function () {
            frappe.show_alert({ message: "Failed to load themes.", indicator: "red" });
        });
    }

    function renderThemeGrid(themes, currentTheme) {
        const loader = document.getElementById("navbar-theme-grid-loader");
        const grid   = document.getElementById("navbar-theme-grid");

        if (!grid) return;

        if (!themes || themes.length === 0) {
            if (loader) loader.innerHTML = `
                <div style="text-align:center;color:#9CA3AF;padding:40px 0;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24"
                         fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:12px;opacity:0.5">
                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                    <p>No active themes found.<br>
                    <a href="/app/navbar-theme/new-navbar-theme-1" target="_blank"
                       style="color:var(--pro-primary,#006269);">Create your first theme →</a></p>
                </div>`;
            return;
        }

        if (loader) loader.style.display = "none";
        grid.style.display = "grid";

        const cards = themes.map(theme => {
            const isSelected = currentTheme && currentTheme.theme_name === theme.theme_name;
            const bgStyle = theme.background_image_url
                ? `background-image:url("${theme.background_image_url}"); background-size:cover; background-position:center;`
                : `background: linear-gradient(135deg, #203535 0%, #006269 100%);`;

            return `
                <div class="navbar-theme-card ${isSelected ? "selected" : ""}"
                     data-theme-name="${escapeHtml(theme.name)}"
                     data-bg="${escapeHtml(theme.background_image_url || "")}"
                     data-text="${escapeHtml(theme.navbar_text_color || "#FFFFFF")}"
                     data-label="${escapeHtml(theme.theme_name)}"
                     title="Click to preview: ${escapeHtml(theme.theme_name)}">
                    <div class="theme-card-preview" style="${bgStyle}">
                        ${isSelected ? '<div class="theme-check-badge">✓</div>' : ""}
                        <div class="theme-card-mini-navbar">
                            <span style="color:${theme.navbar_text_color || "#FFFFFF"};font-size:10px;font-weight:700;">
                                ERPNext
                            </span>
                        </div>
                    </div>
                    <div class="theme-card-label">${escapeHtml(theme.theme_name)}</div>
                </div>`;
        }).join("");

        grid.innerHTML = cards;

        // Bind click handlers
        grid.querySelectorAll(".navbar-theme-card").forEach(card => {
            card.addEventListener("click", function () {
                // Deselect all
                grid.querySelectorAll(".navbar-theme-card").forEach(c => {
                    c.classList.remove("selected");
                    const badge = c.querySelector(".theme-check-badge");
                    if (badge) badge.remove();
                });
                // Select this one
                card.classList.add("selected");
                const preview = card.querySelector(".theme-card-preview");
                if (preview && !preview.querySelector(".theme-check-badge")) {
                    const badge = document.createElement("div");
                    badge.className = "theme-check-badge";
                    badge.textContent = "✓";
                    preview.appendChild(badge);
                }

                // Store selected theme data
                _selectedTheme = {
                    name:       card.dataset.themeName,
                    bg_image:   card.dataset.bg,
                    text_color: card.dataset.text,
                    theme_name: card.dataset.label,
                };

                // Instant CSS preview
                setCSSVariables(_selectedTheme.bg_image, _selectedTheme.text_color);
            });
        });
    }

    function saveTheme(theme, dialog) {
        const isReset = !theme.name;

        frappe.call({
            method: "frappe.client.set_value",
            args: {
                doctype: "User",
                name: frappe.session.user,
                fieldname: "custom_navbar_theme",
                value: theme.name || null,
            },
            callback(r) {
                if (r.exc) {
                    frappe.show_alert({ message: "Failed to save theme.", indicator: "red" });
                    return;
                }
                // Update boot cache for this session
                if (frappe.boot) {
                    frappe.boot.user_theme_details = theme.name ? {
                        theme_name: theme.theme_name,
                        bg_image:   theme.bg_image,
                        text_color: theme.text_color,
                    } : null;
                }

                dialog.hide();
                frappe.show_alert({
                    message: isReset
                        ? "Navbar reset to default."
                        : `Theme "<b>${frappe.utils.escape_html(theme.theme_name)}</b>" applied!`,
                    indicator: "green",
                }, 4);

                // Apply immediately (already previewed, just confirm)
                if (!isReset) {
                    setCSSVariables(theme.bg_image, theme.text_color);
                } else {
                    setCSSVariables("", "#FFFFFF");
                }
            },
        });
    }

    /* ─────────────────────────────────────────────
       UTILITY
    ───────────────────────────────────────────── */
    function escapeHtml(str) {
        return String(str || "")
            .replace(/&/g, "&amp;")
            .replace(/"/g, "&quot;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    /** Retry injection until the navbar dropdown is in the DOM. */
    function tryInjectMenu(attempts) {
        attempts = attempts || 0;
        if (attempts > 30) return; // give up after ~15 s
        injectMenuItems();
        if (!document.getElementById(MENU_ITEM_ID)) {
            setTimeout(() => tryInjectMenu(attempts + 1), 500);
        }
    }

    /* ─────────────────────────────────────────────
       BOOTSTRAP
    ───────────────────────────────────────────── */
    frappe.ready(function () {
        // 1. Apply boot theme (already done by CSS vars on :root at parse time)
        applyBootTheme();

        // 2. Inject menu item with retry
        setTimeout(tryInjectMenu, 800);
    });

    // Re-inject on Frappe SPA route changes (they re-render the dropdown)
    document.addEventListener("page-change", function () {
        // Re-apply CSS vars in case Frappe re-injected its own styles
        applyBootTheme();
        setTimeout(tryInjectMenu, 400);
    });

})();
