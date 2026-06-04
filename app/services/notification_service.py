from datetime import datetime, timedelta
from flask import url_for
from app import db
from app.auth.models import Notification, User

class NotificationService:
    """Service for creating and managing notifications"""
    
    @staticmethod
    def create_notification(user_id, notification_type, title, message, 
                           related_type=None, related_id=None, 
                           priority='normal', metadata=None, expires_in_days=30):
        """Create a single notification"""
        
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            related_type=related_type,
            related_id=related_id,
            priority=priority,
            metadata=metadata or {},
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    
    @staticmethod
    def create_bulk_notifications(user_ids, notification_type, title, message,
                                  related_type=None, related_id=None, 
                                  priority='normal', metadata=None):
        """Create notifications for multiple users"""
        
        notifications = []
        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                related_type=related_type,
                related_id=related_id,
                priority=priority,
                metadata=metadata or {},
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            notifications.append(notification)
        
        db.session.add_all(notifications)
        db.session.commit()
        
        return notifications
    
    @staticmethod
    def get_unread_count(user_id):
        """Get unread notification count for a user"""
        return Notification.query.filter_by(
            user_id=user_id, 
            is_read=False
        ).filter(
            Notification.expires_at > datetime.utcnow()
        ).count()
    
    @staticmethod
    def get_unread_count_by_type(user_id,type):
        """Get unread notification count for a user"""
        return Notification.query.filter_by(
            user_id=user_id, 
            is_read=False,
            
        ).filter(
            Notification.expires_at > datetime.utcnow()
        ).count()
    
    @staticmethod
    def get_recent_notifications(user_id, limit=20):
        """Get recent notifications for a user"""
        return Notification.query.filter_by(
            user_id=user_id
        ).filter(
            Notification.expires_at > datetime.utcnow()
        ).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all notifications as read for a user"""
        Notification.query.filter_by(
            user_id=user_id, 
            is_read=False
        ).update({'is_read': True, 'read_at': datetime.utcnow()})
        db.session.commit()

    @staticmethod
    def mark_as_read_by_type(user_id,related_type):
        """Mark all notifications as read for a user"""
        Notification.query.filter_by(
            user_id=user_id, 
            is_read=False,
            related_type=related_type
        ).update({'is_read': True, 'read_at': datetime.utcnow()})
        db.session.commit()
    
    
    @staticmethod
    def delete_old_notifications(days=60):
        """Delete notifications older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        Notification.query.filter(
            Notification.created_at < cutoff_date,
            Notification.is_read == True
        ).delete()
        db.session.commit()
    
    @staticmethod
    def clean_expired_notifications():
        """Delete expired notifications"""
        Notification.query.filter(
            Notification.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()


# ============================================
# PRE-DEFINED NOTIFICATION TEMPLATES
# ============================================

class NotificationTemplates:
    """Pre-defined notification templates for common actions"""
    
    @staticmethod
    def offer_received(offer):
        """When seller receives a new offer"""
        return {
            'type': 'offer_received',
            'title': 'New Offer Received',
            'message': f'{offer.company.name} has made an offer of ${offer.price:.2f} on your listing "{offer.listing.title[:50]}"',
            'related_type': 'offer',
            'related_id': offer.id,
            'priority': 'high',
            'metadata': {
                'action_url': url_for('offers.received', _external=True),
                'action_text': 'View Offer',
                'icon': 'handshake',
                'amount': float(offer.price)
            }
        }
    
    @staticmethod
    def offer_accepted(offer):
        """When buyer's offer is accepted"""
        return {
            'type': 'offer_accepted',
            'title': 'Offer Accepted!',
            'message': f'Your offer of ${offer.price:.2f} for "{offer.listing.title[:50]}" has been accepted. Transaction created.',
            'related_type': 'transaction',
            'related_id': offer.transaction.id if offer.transaction else None,
            'priority': 'high',
            'metadata': {
                'action_url': url_for('transactions.detail', transaction_id=offer.transaction.id, _external=True) if offer.transaction else '#',
                'action_text': 'View Transaction',
                'icon': 'check-circle'
            }
        }
    
    @staticmethod
    def offer_rejected(offer):
        """When buyer's offer is rejected"""
        return {
            'type': 'offer_rejected',
            'title': 'Offer Declined',
            'message': f'Your offer of ${offer.price:.2f} for "{offer.listing.title[:50]}" was declined by the seller.',
            'related_type': 'offer',
            'related_id': offer.id,
            'priority': 'normal',
            'metadata': {
                'action_url': url_for('offers.index', _external=True),
                'action_text': 'View Offers',
                'icon': 'times-circle'
            }
        }
    
    @staticmethod
    def transaction_created(transaction):
        """When a new transaction is created"""
        return {
            'type': 'transaction_created',
            'title': 'New Transaction Started',
            'message': f'Transaction #{transaction.id} has been created for "{transaction.listing.title[:50]}"',
            'related_type': 'transaction',
            'related_id': transaction.id,
            'priority': 'high',
            'metadata': {
                'action_url': url_for('transactions.detail', transaction_id=transaction.id, _external=True),
                'action_text': 'View Transaction',
                'icon': 'shopping-cart'
            }
        }
    
    @staticmethod
    def payment_received(transaction):
        """When seller receives payment (buyer paid)"""
        return {
            'type': 'payment_received',
            'title': 'Payment Received',
            'message': f'Payment of ${transaction.final_price:.2f} has been received for transaction #{transaction.id}. Ready to ship.',
            'related_type': 'transaction',
            'related_id': transaction.id,
            'priority': 'urgent',
            'metadata': {
                'action_url': url_for('transactions.detail', transaction_id=transaction.id, _external=True),
                'action_text': 'Confirm Shipment',
                'icon': 'dollar-sign'
            }
        }
    
    @staticmethod
    def payment_confirmed(transaction):
        """When seller confirms payment receipt"""
        return {
            'type': 'payment_confirmed',
            'title': 'Payment Confirmed',
            'message': f'Seller has confirmed receipt of payment for transaction #{transaction.id}. Transaction complete!',
            'related_type': 'transaction',
            'related_id': transaction.id,
            'priority': 'high',
            'metadata': {
                'action_url': url_for('transactions.detail', transaction_id=transaction.id, _external=True),
                'action_text': 'View Transaction',
                'icon': 'check-double'
            }
        }
    
    @staticmethod
    def new_message(conversation, sender, message_preview):
        """When user receives a new message"""
        return {
            'type': 'message',
            'title': f'New message from {sender.full_name}',
            'message': message_preview[:100],
            'related_type': 'conversation',
            'related_id': conversation.id,
            'priority': 'normal',
            'metadata': {
                'action_url': url_for('messages.thread', conversation_id=conversation.id, _external=True),
                'action_text': 'View Message',
                'icon': 'envelope',
                'sender_name': sender.full_name
            }
        }
    
    @staticmethod
    def listing_expired(listing):
        """When a listing expires"""
        return {
            'type': 'listing_expired',
            'title': 'Listing Expired',
            'message': f'Your listing "{listing.title[:50]}" has expired. Renew it to keep it active.',
            'related_type': 'listing',
            'related_id': listing.id,
            'priority': 'normal',
            'metadata': {
                'action_url': url_for('listings.edit_listing', listing_id=listing.id, _external=True),
                'action_text': 'Renew Listing',
                'icon': 'clock'
            }
        }
    
    @staticmethod
    def listing_approved(listing):
        """When listing is approved by admin"""
        return {
            'type': 'listing_approved',
            'title': 'Listing Approved',
            'message': f'Your listing "{listing.title[:50]}" has been approved and is now live!',
            'related_type': 'listing',
            'related_id': listing.id,
            'priority': 'normal',
            'metadata': {
                'action_url': url_for('listings.detail', listing_id=listing.id, _external=True),
                'action_text': 'View Listing',
                'icon': 'check'
            }
        }
    
    @staticmethod
    def listing_rejected(listing, reason):
        """When listing is rejected by admin"""
        return {
            'type': 'listing_rejected',
            'title': 'Listing Rejected',
            'message': f'Your listing "{listing.title[:50]}" was rejected. Reason: {reason}',
            'related_type': 'listing',
            'related_id': listing.id,
            'priority': 'high',
            'metadata': {
                'action_url': url_for('listings.edit_listing', listing_id=listing.id, _external=True),
                'action_text': 'Edit Listing',
                'icon': 'ban',
                'reason': reason
            }
        }
    
    @staticmethod
    def subscription_expiring(company, days_left):
        """When subscription is about to expire"""
        return {
            'type': 'system',
            'title': 'Subscription Expiring Soon',
            'message': f'Your subscription will expire in {days_left} days. Renew to continue enjoying premium features.',
            'related_type': 'company',
            'related_id': company.id,
            'priority': 'high',
            'metadata': {
                'action_url': url_for('subscription.billing', _external=True),
                'action_text': 'Renew Now',
                'icon': 'exclamation-triangle',
                'days_left': days_left
            }
        }