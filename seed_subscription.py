from app import app

from app.subscription.models import SubscriptionPlan
from app import db
def seed_subscription_plans():
    """Seed initial subscription plans"""
    
    plans = [
        {
            'name': 'Free',
            'slug': 'free',
            'description': 'Perfect for occasional sellers',
            'price_monthly': 0,
            'price_yearly': 0,
            'max_active_listings': 3,
            'max_featured_listings': 0,
            'max_team_members': 1,
            'max_monthly_transactions': 10,
            'commission_rate': 0.0,
            'has_analytics': False,
            'has_api_access': False,
            'has_priority_support': False,
            'has_bulk_upload': False,
            'has_advanced_filters': False,
            'sort_order': 1,
            'is_popular': False
        },
        {
            'name': 'Basic',
            'slug': 'basic',
            'description': 'For growing businesses',
            'price_monthly': 1500,
            'price_yearly': 15300,
            'max_active_listings': 20,
            'max_featured_listings': 2,
            'max_team_members': 3,
            'max_monthly_transactions': 50,
            'commission_rate': 0.0,
            'has_analytics': True,
            'has_api_access': False,
            'has_priority_support': True,
            'has_bulk_upload': False,
            'has_advanced_filters': True,
            'sort_order': 2,
            'is_popular': True
        },
        {
            'name': 'Pro',
            'slug': 'pro',
            'description': 'For high-volume sellers',
            'price_monthly': 3000,
            'price_yearly': 30600,
            'max_active_listings': 100,
            'max_featured_listings': 10,
            'max_team_members': 10,
            'max_monthly_transactions': 500,
            'commission_rate': 0.0,
            'has_analytics': True,
            'has_api_access': True,
            'has_priority_support': True,
            'has_bulk_upload': True,
            'has_advanced_filters': True,
            'sort_order': 3,
            'is_popular': False
        },
        {
            'name': 'Enterprise',
            'slug': 'enterprise',
            'description': 'Custom solutions for large enterprises',
            'price_monthly': 5999,
            'price_yearly': 61189,
            'max_active_listings': 999999,
            'max_featured_listings': 50,
            'max_team_members': 999999,
            'max_monthly_transactions': 999999,
            'commission_rate': 0.0,
            'has_analytics': True,
            'has_api_access': True,
            'has_priority_support': True,
            'has_bulk_upload': True,
            'has_advanced_filters': True,
            'has_dedicated_manager': True,
            'sort_order': 4,
            'is_popular': False
        }
    ]
    
    for plan_data in plans:
        existing = SubscriptionPlan.query.filter_by(slug=plan_data['slug']).first()
        if not existing:
            plan = SubscriptionPlan(**plan_data)
            db.session.add(plan)
            print(f"Added plan: {plan_data['name']}")
    
    db.session.commit()
    print("Subscription plans seeded successfully!")


def update_existing_companies_to_free():
    """Set all existing companies to free tier"""
    from app.auth.models import Company
    
    free_plan = SubscriptionPlan.query.filter_by(slug='free').first()
    
    companies = Company.query.all()
    for company in companies:
        company.subscription_plan_id = free_plan.id
        company.subscription_status = 'free'
        company.max_active_listings = free_plan.max_active_listings
        company.max_featured_listings = free_plan.max_featured_listings
        company.max_team_members = free_plan.max_team_members
        company.max_monthly_transactions = free_plan.max_monthly_transactions
        company.commission_rate = free_plan.commission_rate
    
    db.session.commit()
    print(f"Updated {len(companies)} companies to free tier")
with app.app_context():
    seed_subscription_plans()
    update_existing_companies_to_free()