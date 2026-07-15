app_name = "custom_ui"
app_title = "Custom UI PRO"
app_publisher = "Grutika"
app_description = "Custom UI"
app_name = "custom_ui"
app_title = "Custom UI PRO"
app_publisher = "Grutika"
app_description = "Custom UI"
app_email = "grutika@example.com"
app_license = "mit"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = ["/assets/custom_ui/css/minimal_desk_v9.css"]
app_include_js = [
    "/assets/custom_ui/js/breadcrumb_chevron_fix.js",
    "/assets/custom_ui/js/ai_navigation.js"
]

# include js, css files in header of web template
web_include_css = ["/assets/custom_ui/css/minimal_desk_v9.css"]

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "custom_ui/public/scss/website"

fixtures = ["Client Script", "AI Model Rate"]

scheduler_events = {
    "daily": [
        "custom_ui.custom_ui.ai_chat.budget.sync_exchange_rate"
    ]
}
