"""
MACH-1 Notifications via ntfy.sh
Free push notifications to phone/desktop.
"""
import requests
from config import settings
from utils.logger import get_logger

log = get_logger("mach1.notify")

# Priority levels
PRIORITY_MIN = 1
PRIORITY_LOW = 2
PRIORITY_DEFAULT = 3
PRIORITY_HIGH = 4
PRIORITY_URGENT = 5

# Event → priority mapping
EVENT_PRIORITY = {
    "content_ready": PRIORITY_DEFAULT,
    "project_building": PRIORITY_LOW,
    "project_eta": PRIORITY_LOW,
    "project_complete": PRIORITY_HIGH,
    "review_done": PRIORITY_DEFAULT,
    "git_push_pending": PRIORITY_HIGH,
    "self_fix_attempt": PRIORITY_LOW,
    "api_rate_limit": PRIORITY_DEFAULT,
    "api_down": PRIORITY_HIGH,
    "agent_crashed": PRIORITY_URGENT,
    "project_failed": PRIORITY_HIGH,
    "disk_low": PRIORITY_HIGH,
    "backup_done": PRIORITY_MIN,
    "health_report": PRIORITY_LOW,
    "plan_proposed": PRIORITY_HIGH,
    "outreach_ready": PRIORITY_DEFAULT,
}

# Event → emoji
EVENT_TAGS = {
    "content_ready": "memo",
    "project_building": "hammer",
    "project_complete": "white_check_mark",
    "project_failed": "x",
    "agent_crashed": "rotating_light",
    "api_down": "warning",
    "backup_done": "floppy_disk",
    "health_report": "heartbeat",
    "plan_proposed": "clipboard",
    "git_push_pending": "rocket",
    "outreach_ready": "envelope",
}


def notify(event: str, title: str, message: str, url: str = None) -> bool:
    """
    Send a push notification via ntfy.sh.

    Args:
        event: Event type key (maps to priority/emoji)
        title: Notification title
        message: Notification body
        url: Optional click URL

    Returns:
        True if sent successfully
    """
    if not settings.NTFY_TOPIC:
        log.debug("Notifications disabled (no NTFY_TOPIC)")
        return False

    priority = EVENT_PRIORITY.get(event, PRIORITY_DEFAULT)
    tags = EVENT_TAGS.get(event, "bell")

    headers = {
        "Title": title,
        "Priority": str(priority),
        "Tags": tags,
    }

    if url:
        headers["Click"] = url

    try:
        resp = requests.post(
            f"{settings.NTFY_SERVER}/{settings.NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        log.info(f"Notification sent: [{event}] {title}")
        return True
    except Exception as e:
        log.warning(f"Notification failed: {e}")
        return False


def notify_content_ready(count: int):
    notify("content_ready", "Content Ready", f"{count} new items ready for review")


def notify_project_complete(name: str):
    notify("project_complete", "Project Complete", f"'{name}' built successfully")


def notify_project_failed(name: str, reason: str):
    notify("project_failed", "Project Failed", f"'{name}' failed: {reason}")


def notify_plan_proposed(summary: str):
    notify(
        "plan_proposed",
        "CEO Plan Proposed",
        f"New plan awaiting your approval:\n{summary}",
        url=f"http://localhost:{settings.FLASK_PORT}/plans",
    )


def notify_agent_crashed(agent: str, error: str):
    notify("agent_crashed", f"Agent Crashed: {agent}", error[:200])


def notify_health_report(summary: str):
    notify("health_report", "Nightly Health Report", summary)
