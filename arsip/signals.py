import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

logger = logging.getLogger('arsip.auth')

@receiver(user_logged_in)
def log_user_logged_in(sender, request, user, **kwargs):
    username = user.get_username() if user else 'unknown'
    logger.info("Authentication success: user '%s' logged in.", username)

@receiver(user_logged_out)
def log_user_logged_out(sender, request, user, **kwargs):
    username = user.get_username() if user else 'anonymous'
    logger.info("Authentication logout: user '%s' logged out.", username)

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get('username', 'unknown') if isinstance(credentials, dict) else 'unknown'
    logger.warning("Authentication failure: failed login attempt for username '%s'.", username)
