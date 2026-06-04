from flask import current_app
from app.services.notification_service import NotificationService
from app.auth.models import Notification

def inject_notifications():
    """Make notifications available in all templates"""
    
    def get_notifications(user_id=None):
        if user_id:
            return NotificationService.get_recent_notifications(user_id)
        return []
    
    def get_unread_count(user_id=None):
        if user_id:
            return NotificationService.get_unread_count(user_id)
        return 0
    
    def get_notification_badge(user):
        """Get notification data for a user"""
        if not user or not user.is_authenticated:
            return {'count': 0, 'notifications': []}
        
        return {
            'count': NotificationService.get_unread_count(user.id),
            'notifications': NotificationService.get_recent_notifications(user.id, limit=10)
        }
    
    return {
        'notification_badge': get_notification_badge,
        'get_notifications': get_notifications,
        'get_unread_count': get_unread_count
    }


def inject_notification_service():
    """Make notification service available in templates"""
    from app.services.notification_service import NotificationService
    return {'NotificationService': NotificationService}