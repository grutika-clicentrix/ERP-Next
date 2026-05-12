/**
 * Breadcrumb Chevron Force-White Fix
 * 
 * This script injects a <style> block at the END of the document <head>
 * AFTER all other stylesheets have loaded. This guarantees our rules win
 * the CSS specificity battle against Frappe's desk.bundle.css.
 */
(function () {
    function injectBreadcrumbStyles() {
        const styleId = 'custom-ui-breadcrumb-fix';
        if (document.getElementById(styleId)) return;

        const style = document.createElement('style');
        style.id = styleId;
        // Use maximum specificity: html body .navbar ul#navbar-breadcrumbs
        style.textContent = `
            /* =========================================
               Custom UI: Force breadcrumb separators WHITE
               Injected AFTER all other stylesheets to win specificity
               ========================================= */

            /* The separator is a ::before pseudo-element on li + li */
            html body .navbar ul#navbar-breadcrumbs li + li::before,
            html body ul#navbar-breadcrumbs li + li::before {
                color: #FFFFFF !important;
                opacity: 1 !important;
            }

            /* All pseudo-elements within breadcrumbs */
            html body ul#navbar-breadcrumbs li::before,
            html body ul#navbar-breadcrumbs li::after {
                color: #FFFFFF !important;
                opacity: 1 !important;
            }

            /* SVG-based separators */
            html body ul#navbar-breadcrumbs svg,
            html body ul#navbar-breadcrumbs .breadcrumb-separator svg,
            html body ul#navbar-breadcrumbs .breadcrumb-separator {
                fill: #FFFFFF !important;
                stroke: #FFFFFF !important;
                color: #FFFFFF !important;
                filter: brightness(0) invert(1) !important;
                opacity: 1 !important;
            }
        `;
        document.head.appendChild(style);
    }

    // Run immediately if DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectBreadcrumbStyles);
    } else {
        injectBreadcrumbStyles();
    }

    // Also re-run on Frappe page change (SPA navigation)
    if (window.frappe) {
        frappe.router && frappe.router.on && frappe.router.on('change', injectBreadcrumbStyles);
    }
    document.addEventListener('page-change', injectBreadcrumbStyles);
})();
