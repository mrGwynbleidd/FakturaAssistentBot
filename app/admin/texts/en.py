ADMIN_TEXTS_EN = {

    #main menu
    "admin_menu_title": "Admin-Panel",
    "admin_menu_decription": "Choose an action",
    "access_denied": "You do not have access to admin panel",
    "unknown_command": "Unknown admin command",

    #main buttons
    "btn_add_qa": "➕ Add Q/A",
    "btn_add_incident": "🚨 Add temporary issue",
    "btn_active_incidents": "📋 Active issues",
    "btn_review_cases": "✅ Review cases",
    "btn_stats": "📊 Statistics",
    "btn_settings": "⚙️ Settings",
    "btn_cancel": "❌ Cancel",
    "btn_back": "⬅️ Back",
    "btn_exit": "⬅️ Exit",

    # Confirmation buttons
    "btn_confirm": "✅ Confirm",
    "btn_reject": "❌ Reject",
    "btn_skip": "⏭ Skip",

    # Add Q/A
    "add_qa_start": "Creating a new Q/A.",
    "enter_question": "Enter the question a user may ask:",
    "enter_answer": "Enter the correct answer for this question:",
    "enter_category": "Enter a category. Example: login, documents, soliq, api, general.",
    "enter_tags": "Enter keywords separated by commas. Example: ttn, invoice, document.",
    "qa_preview_title": "Review the Q/A before saving:",
    "qa_saved": "Q/A saved successfully.",
    "qa_cancelled": "Q/A creation cancelled.",

    # Incidents
    "add_incident_start": "Creating a temporary issue.",
    "enter_incident_title": "Enter the issue title. Example: Soliq outage.",
    "enter_incident_problem": "Briefly describe the issue:",
    "enter_incident_keywords": "Enter keywords separated by commas. Example: soliq, error, sending.",
    "enter_incident_answer": "Enter the answer the bot should show to users:",
    "enter_incident_end_time": "Enter the end time. Example: 2026-06-16 18:00. If unknown, write: none.",
    "incident_preview_title": "Review the temporary issue before activation:",
    "incident_saved": "Temporary issue saved and activated.",
    "incident_cancelled": "Temporary issue creation cancelled.",
    "no_active_incidents": "There are no active temporary issues.",
    "active_incidents_title": "Active temporary issues:",
    "incident_disabled": "Temporary issue disabled.",
    "incident_not_found": "Temporary issue not found.",

    # Review
    "review_cases_title": "Cases pending review:",
    "no_review_cases": "There are no cases pending review.",
    "enter_review_answer": "Enter the correct answer for this case:",
    "review_case_saved": "Case saved to approved.csv.",
    "review_case_rejected": "Case rejected.",
    "review_case_not_found": "Case not found.",

    # Stats
    "stats_title": "Bot statistics",
    "stats_empty": "No statistics data yet.",

    # Common
    "saved_successfully": "Saved successfully.",
    "operation_cancelled": "Operation cancelled.",
    "error_occurred": "An error occurred. Check the logs.",

    # Settings / Admin management
    "settings_title": "⚙️ Settings",
    "btn_list_admins": "👥 Admin list",
    "btn_add_admin": "➕ Add admin",
    "btn_remove_admin": "➖ Remove admin",
    "admin_list_title": "👥 Current admins:",
    "admin_list_empty": "No file-based admins. Check ADMIN_IDS in config.",
    "enter_admin_id": "Enter the Telegram ID of the new admin (digits only).\n\nTo find out an ID, send @userinfobot a message in Telegram.",
    "admin_added": "✅ Admin added.",
    "admin_already_exists": "⚠️ This user is already an admin.",
    "enter_remove_admin_id": "Enter the Telegram ID of the admin to remove:",
    "admin_removed": "✅ Admin removed.",
    "admin_not_found": "❌ That Telegram ID was not found in the file.",
    "admin_env_warning": "⚠️ Admins from ADMIN_IDS (config/env) cannot be removed via the bot.",
    "invalid_admin_id": "❌ Invalid format. Enter a numeric Telegram ID.",
    "btn_manage_admins": "👥 Manage admins",
    "self_remove_error": "❌ You cannot remove yourself from the admin list.",
}
