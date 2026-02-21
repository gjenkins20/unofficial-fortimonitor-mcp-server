"""Login handler for web application authentication.

Tries generic username/password form selectors first, then falls back
to FortiMonitor-specific selectors.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Generic login form selectors (tried in order)
_GENERIC_USERNAME_SELECTORS = [
    'input[name="username"]',
    'input[name="email"]',
    'input[name="user"]',
    'input[name="login"]',
    'input[type="email"]',
    'input[id="username"]',
    'input[id="email"]',
    'input[id="login"]',
]

_GENERIC_PASSWORD_SELECTORS = [
    'input[name="password"]',
    'input[name="pass"]',
    'input[type="password"]',
    'input[id="password"]',
]

_GENERIC_SUBMIT_SELECTORS = [
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("Log in")',
    'button:has-text("Login")',
    'button:has-text("Sign in")',
    'button:has-text("Sign In")',
    '#login-button',
    '.login-btn',
]

# FortiMonitor-specific selectors (fallback)
_FORTI_USERNAME_SELECTORS = [
    'input[name="email"]',
    '#inputEmail',
    'input[placeholder*="email"]',
]

_FORTI_PASSWORD_SELECTORS = [
    'input[name="password"]',
    '#inputPassword',
    'input[placeholder*="password"]',
]

_FORTI_SUBMIT_SELECTORS = [
    'button[type="submit"]',
    '#login-button',
    'button:has-text("Log In")',
]


async def _try_selectors(page, selectors: list) -> Optional[str]:
    """Try a list of selectors and return the first one that matches a visible element."""
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.is_visible(timeout=500):
                return selector
        except Exception:
            continue
    return None


async def authenticate(
    page,
    login_url: str,
    username: str,
    password: str,
    timeout: int = 30000,
) -> bool:
    """Authenticate with a web application.

    Navigates to the login URL, finds username/password fields, fills them,
    and submits the form. Tries generic selectors first, then FortiMonitor-
    specific ones.

    Args:
        page: Playwright Page instance.
        login_url: URL of the login page.
        username: Login username/email.
        password: Login password.
        timeout: Maximum wait time in ms for navigation and elements.

    Returns:
        True if authentication appears successful (page navigated away from login).
    """
    logger.info(f"Navigating to login page: {login_url}")
    await page.goto(login_url, wait_until="networkidle", timeout=timeout)

    # Find username field
    user_selector = await _try_selectors(
        page, _GENERIC_USERNAME_SELECTORS + _FORTI_USERNAME_SELECTORS
    )
    if not user_selector:
        logger.error("Could not find username field")
        return False

    # Find password field
    pass_selector = await _try_selectors(
        page, _GENERIC_PASSWORD_SELECTORS + _FORTI_PASSWORD_SELECTORS
    )
    if not pass_selector:
        logger.error("Could not find password field")
        return False

    # Find submit button
    submit_selector = await _try_selectors(
        page, _GENERIC_SUBMIT_SELECTORS + _FORTI_SUBMIT_SELECTORS
    )
    if not submit_selector:
        logger.error("Could not find submit button")
        return False

    logger.info(
        f"Found login form fields: user={user_selector}, "
        f"pass={pass_selector}, submit={submit_selector}"
    )

    # Fill credentials and submit
    await page.locator(user_selector).first.fill(username)
    await page.locator(pass_selector).first.fill(password)
    await page.locator(submit_selector).first.click()

    # Wait for navigation away from login page
    try:
        await page.wait_for_url(
            lambda url: url != login_url, timeout=timeout
        )
        logger.info(f"Authentication successful, now at: {page.url}")
        return True
    except Exception:
        logger.warning(
            f"Authentication may have failed — still at: {page.url}"
        )
        return False
