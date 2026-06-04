from datetime import datetime, timedelta
from flask import current_app
from app.subscription.models import SubscriptionPlan, SubscriptionPayment
from app.auth.models import Company, User
from app.listings.models import Item as Listing
from app import db

class SubscriptionService:
    """Service class for subscription operations"""
    
    @staticmethod
    def get_plan_by_id(plan_id):
        """Get subscription plan by ID"""
        return SubscriptionPlan.query.get(plan_id)
    
    @staticmethod
    def get_plan_by_slug(slug):
        """Get subscription plan by slug"""
        return SubscriptionPlan.query.filter_by(slug=slug).first()
    
    @staticmethod
    def get_free_plan():
        """Get the free plan"""
        return SubscriptionPlan.query.filter_by(slug='free').first()
    
    @staticmethod
    def activate_subscription(company_id, plan_id, interval='monthly', payment_id=None):
        """Activate a subscription for a company"""
        
        company = Company.query.get(company_id)
        plan = SubscriptionPlan.query.get(plan_id)
        
        if not company or not plan:
            return False
        
        # Calculate dates
        now = datetime.utcnow()
        if interval == 'yearly':
            end_date = now + timedelta(days=365)
            price = plan.price_yearly
        else:
            end_date = now + timedelta(days=30)
            price = plan.price_monthly
        
        # Update company
        company.subscription_plan_id = plan.id
        company.subscription_status = 'active'
        company.subscription_started_at = now
        company.subscription_ends_at = end_date
        company.max_active_listings = plan.max_active_listings
        company.max_featured_listings = plan.max_featured_listings
        company.max_team_members = plan.max_team_members
        company.max_monthly_transactions = plan.max_monthly_transactions
        company.commission_rate = plan.commission_rate
        company.auto_renew = True
        
        # Create payment record if not exists
        if payment_id:
            payment = SubscriptionPayment.query.get(payment_id)
            if payment:
                payment.status = 'succeeded'
                payment.paid_at = now
        
        db.session.commit()
        
        return True
    
    @staticmethod
    def downgrade_to_free(company_id):
        """Downgrade company to free plan"""
        
        company = Company.query.get(company_id)
        free_plan = SubscriptionService.get_free_plan()
        
        if not company or not free_plan:
            return False
        
        company.subscription_plan_id = free_plan.id
        company.subscription_status = 'free'
        company.max_active_listings = free_plan.max_active_listings
        company.max_featured_listings = free_plan.max_featured_listings
        company.max_team_members = free_plan.max_team_members
        company.max_monthly_transactions = free_plan.max_monthly_transactions
        company.commission_rate = free_plan.commission_rate
        
        db.session.commit()
        
        return True
    
    @staticmethod
    def check_limits(company_id):
        """Check if company has exceeded any limits and return warnings"""
        
        company = Company.query.get(company_id)
        if not company:
            return []
        
        warnings = []
        
        # Check listing limit
        active_listings = Listing.query.filter_by(company_id=company.id, status='active').count()
        if active_listings >= company.max_active_listings:
            warnings.append({
                'type': 'listings',
                'message': f'You have reached your listing limit ({active_listings}/{company.max_active_listings}). Upgrade to post more.',
                'current': active_listings,
                'limit': company.max_active_listings
            })
        
        # Check team member limit
        team_members = User.query.filter_by(company_id=company.id).count()
        if team_members >= company.max_team_members:
            warnings.append({
                'type': 'team',
                'message': f'You have reached your team member limit ({team_members}/{company.max_team_members}). Upgrade to add more users.',
                'current': team_members,
                'limit': company.max_team_members
            })
        
        return warnings
    
    @staticmethod
    def create_invoice(company, payment):
        """Generate invoice data"""
        
        invoice_data = {
            'invoice_number': payment.invoice_number,
            'date': payment.created_at.strftime('%B %d, %Y'),
            'company_name': company.name,
            'company_address': f"{company.address_line1}, {company.city}, {company.country}",
            'plan_name': payment.subscription_plan.name,
            'period': f"{payment.period_start.strftime('%B %d, %Y')} - {payment.period_end.strftime('%B %d, %Y')}",
            'amount': payment.amount,
            'currency': payment.currency,
            'status': payment.status
        }
        
        return invoice_data