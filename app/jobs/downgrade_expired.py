# app/jobs/downgrade_expired.py

from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.auth.models import Company
from app.subscription.models import SubscriptionPlan
from app.listings.models import Item as Listing
from app.services.notification_service import NotificationService

def process_expired_subscriptions():
    """Run daily to process expired subscriptions"""
    print("--------------------------------------------cronjobrun")
    # Companies with expired subscriptions (no grace period left)
    expired_companies = Company.query.filter(
        Company.subscription_ends_at < datetime.utcnow(),
        Company.subscription_status == 'active',
        Company.subscription_grace_period_ends < datetime.utcnow()
    ).all()
    print(expired_companies)
    free_plan = SubscriptionPlan.query.filter_by(slug='free').first()
    
    for company in expired_companies:
        # Downgrade to free
        company.subscription_plan_id = free_plan.id
        company.subscription_status = 'expired'
        company.max_active_listings = free_plan.max_active_listings
        company.max_featured_listings = free_plan.max_featured_listings
        company.max_team_members = free_plan.max_team_members
        company.commission_rate = free_plan.commission_rate
        
        # Archive excess listings
        active_listings = Listing.query.filter_by(
            company_id=company.id,
            status='active'
        ).count()
        
        if active_listings > free_plan.max_active_listings:
            excess = active_listings - free_plan.max_active_listings
            listings = Listing.query.filter_by(
                company_id=company.id,
                status='active'
            ).order_by(Listing.created_at).limit(excess).all()
            
            for listing in listings:
                listing.status = 'archived'
        
        db.session.commit()
        
        # Send notification
        NotificationService.create_notification(
            user_id=company.users.id,
            notification_type='subscription_expired',
            title='Subscription Expired',
            message='Your subscription has expired and you have been downgraded to the Free plan.',
            priority='high'
        )
    
    # Start grace period for recently expired
    grace_period_candidates = Company.query.filter(
        Company.subscription_ends_at < datetime.utcnow(),
        Company.subscription_status == 'active',
        Company.subscription_grace_period_used == False
    ).all()
    print("-------------------------------grace period candidates")
    print(grace_period_candidates)
    
    for company in grace_period_candidates:
        company.start_grace_period(days=14)
        db.session.commit()
        
        # Send notification
        NotificationService.create_notification(
            user_id=company.users.id,
            notification_type='subscription_grace_period',
            title='Subscription Expired - Grace Period Started',
            message='Your subscription has expired. You have 14 days of grace period to renew.',
            priority='high'
        )

def process_expired_listing():
    """Run daily to process expired subscriptions"""
    print("--------------------------------------------cronjobrun")
    # Companies with expired subscriptions (no grace period left)
    expired_listing = Listing.query.filter(
        Listing.expires_at < datetime.utcnow(),
        Listing.status == 'active',
        
    ).all()

    for listing in expired_listing:
        listing.status="expired"
        NotificationService.create_notification(
            user_id=listing.manager.id,
            notification_type='listing_expired',
            title='Listing Expired',
            message='Your listing titled 'listing.name' has expired. You have 14 days of grace period to renew.',
            priority='high'
        )
