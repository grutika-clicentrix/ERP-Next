"""
boot.py - Custom UI PRO
=======================
Boot-info injection hook for the Dynamic Navbar Banner Theme feature.

Register this in hooks.py under:
    extend_bootinfo = "custom_ui.custom_ui.boot.inject_user_theme"
"""

import frappe


def inject_user_theme(bootinfo):
    """
    Reads the current user's `custom_navbar_theme` preference.
    """
    bootinfo.user_theme_details = None
    try:
        # Guests have no theme preference
        if frappe.session.user == "Guest":
            return

        # Check if field exists first to avoid crash
        if not frappe.db.has_column("User", "custom_navbar_theme"):
            return

        # Fetch the linked theme name from the User doc
        user_theme = frappe.db.get_value(
            "User",
            frappe.session.user,
            "custom_navbar_theme"
        )

        if not user_theme:
            return

        # Fetch the Navbar Theme document fields
        if not frappe.db.exists("DocType", "Navbar Theme"):
            return

        theme = frappe.db.get_value(
            "Navbar Theme",
            user_theme,
            ["name", "theme_name", "background_image_url", "navbar_text_color", "is_active"],
            as_dict=True,
        )

        if not theme or not theme.is_active:
            return

        bootinfo.user_theme_details = {
            "theme_name": theme.theme_name,
            "bg_image": theme.background_image_url or "",
            "text_color": theme.navbar_text_color or "#FFFFFF",
        }

    except Exception:
        # Never let a theme error crash the boot sequence
        bootinfo.user_theme_details = None
