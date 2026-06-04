from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def subscription_required(feature=None):
    """Decorator to check if user has required subscription feature"""
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please login to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            company = current_user.company
            
            if feature == 'listing':
                if not company.can_create_listing():
                    flash('You have reached your listing limit. Upgrade to post more listings.', 'warning')
                    return redirect(url_for('subscription.pricing'))
            
            elif feature == 'team':
                if not company.can_add_team_member():
                    flash('You have reached your team member limit. Upgrade to add more users.', 'warning')
                    return redirect(url_for('subscription.pricing'))
            
            elif feature == 'analytics':
                if not company.subscription_plan or not company.subscription_plan.has_analytics:
                    flash('Analytics are only available on paid plans. Upgrade to access.', 'warning')
                    return redirect(url_for('subscription.pricing'))
            
            elif feature == 'api':
                if not company.subscription_plan or not company.subscription_plan.has_api_access:
                    flash('API access is only available on Pro and Enterprise plans.', 'warning')
                    return redirect(url_for('subscription.pricing'))
            
            elif feature == 'bulk_upload':
                if not company.subscription_plan or not company.subscription_plan.has_bulk_upload:
                    flash('Bulk upload is only available on Pro and Enterprise plans.', 'warning')
                    return redirect(url_for('subscription.pricing'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def active_subscription_required(f):
    """Decorator to check if user has active subscription"""
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        company = current_user.company
        
        if not company.has_active_subscription():
            flash('This feature requires an active subscription. Please upgrade to continue.', 'warning')
            return redirect(url_for('subscription.pricing'))
        
        return f(*args, **kwargs)
    
    return decorated_function