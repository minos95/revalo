from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.admin import bp
from app.admin.forms import AdminSettingsForm, CategoryAttributeForm, CategoryForm, ModerationForm, SubscriptionPlanForm
from app.auth.models import User, Company
from app.listings.models import Item,Category, Quality_attribute_options, Quality_attributes
from app.transactions.models import Transaction
from app.offers.models import Offer
from app.subscription.models import SubscriptionPlan,SubscriptionPayment
from app import db

# ============================================
# ADMIN DECORATOR
# ============================================

def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'super_admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# ============================================
# DASHBOARD
# ============================================

@bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard with key metrics"""
    
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Stats
    total_users = User.query.count()
    total_companies = Company.query.count()
    total_listings = Item.query.count()
    active_listings = Item.query.filter_by(status='active').count()
    total_transactions = Transaction.query.count()
    completed_transactions = Transaction.query.filter_by(status='completed').count()
    
    # Revenue
    total_revenue = db.session.query(func.sum(SubscriptionPayment.amount)).scalar() or 0
    
    monthly_revenue = db.session.query(func.sum(Transaction.price)).filter(
        Transaction.status == 'completed',
        Transaction.completed_at >= month_ago
    ).scalar() or 0
    
    # Pending items
    pending_listings = Item.query.filter_by(status='pending').count()
    pending_offers = Offer.query.filter_by(status='pending').count()
    pending_disputes = Transaction.query.filter_by(status='disputed').count()
    
    # Recent activity
    recent_users = User.query.order_by(desc(User.created_at)).limit(5).all()
    recent_listings = Item.query.order_by(desc(Item.created_at)).limit(5).all()
    recent_transactions = Transaction.query.order_by(desc(Transaction.created_at)).limit(5).all()
    
    # Charts data
    # Last 7 days signups
    signups_weekly = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = User.query.filter(func.date(User.created_at) == date).count()
        signups_weekly.append({
            'date': date.strftime('%a'),
            'count': count
        })
    
    # Last 7 days revenue
    revenue_weekly = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        revenue = db.session.query(func.sum(Transaction.price)).filter(
            Transaction.status == 'completed',
            func.date(Transaction.completed_at) == date
        ).scalar() or 0
        revenue_weekly.append({
            'date': date.strftime('%a'),
            'revenue': float(revenue)
        })
    
    # Top categories
    top_categories = db.session.query(
        Category.name,
        func.count(Item.id).label('count')
    ).join(Item).group_by(Category.id).order_by(desc('count')).limit(5).all()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_companies=total_companies,
                         total_listings=total_listings,
                         active_listings=active_listings,
                         total_transactions=total_transactions,
                         completed_transactions=completed_transactions,
                         total_revenue=total_revenue,
                         monthly_revenue=monthly_revenue,
                         pending_listings=pending_listings,
                         pending_offers=pending_offers,
                         pending_disputes=pending_disputes,
                         recent_users=recent_users,
                         recent_listings=recent_listings,
                         recent_transactions=recent_transactions,
                         signups_weekly=signups_weekly,
                         revenue_weekly=revenue_weekly,
                         top_categories=top_categories)


# ============================================
# USERS MANAGEMENT
# ============================================

@bp.route('/users')
@admin_required
def users():
    """Manage all users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            User.email.ilike(f'%{search}%') |
            User.first_name.ilike(f'%{search}%') |
            User.last_name.ilike(f'%{search}%')
        )
    
    pagination = query.order_by(desc(User.created_at)).paginate(page=page, per_page=per_page)
    users = pagination.items
    
    return render_template('users.html', users=users, pagination=pagination, search=search)


@bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Activate/deactivate user"""
    user = User.query.get_or_404(user_id)
    
    if  user.status=='active':
        print('+++++++++++++')
        user.status="suspended"
    else:
        print('----------------')
        user.status="active"
    db.session.commit()
    
    status = 'active' if not user.is_active else 'deactivated'
    flash(f'User {user.email} has been {status}.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/users/<int:user_id>/change-role', methods=['POST'])
@admin_required
def change_user_role(user_id):
    """Change user role"""
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    if new_role in ['member', 'admin', 'owner']:
        user.role = new_role
        db.session.commit()
        flash(f'Role changed to {new_role}.', 'success')
    
    return redirect(url_for('admin.users'))


# ============================================
# COMPANIES MANAGEMENT
# ============================================

@bp.route('/companies')
@admin_required
def companies():
    """Manage all companies"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    verification = request.args.get('verification', '')
    
    subscription_plan=SubscriptionPlan.query.all()
    
    query = Company.query
    
    if search:
        query = query.filter(
            Company.name.ilike(f'%{search}%') |
            Company.email.ilike(f'%{search}%')
        )
    
    if verification == 'verified':
        query = query.filter_by(verified=True)
    elif verification == 'pending':
        query = query.filter_by(verified=False)
    
    pagination = query.order_by(desc(Company.created_at)).paginate(page=page, per_page=per_page)
    companies = pagination.items
    
    return render_template('companies.html', companies=companies, pagination=pagination, 
                         search=search, verification=verification,subscription_plan=subscription_plan)


@bp.route('/companies/<int:company_id>/verify', methods=['POST'])
@admin_required
def verify_company(company_id):
    """Verify a company"""
    company = Company.query.get_or_404(company_id)
    company.verified = True
    company.verified_at = datetime.utcnow()
    company.verified_by = current_user.id
    company.status="active"
    db.session.commit()
    
    flash(f'Company {company.name} has been verified.', 'success')
    return redirect(url_for('admin.companies'))


@bp.route('/companies/<int:company_id>/unverify', methods=['POST'])
@admin_required
def unverify_company(company_id):
    """Unverify a company"""
    company = Company.query.get_or_404(company_id)
    company.verified = False
    company.status="suspended"
    db.session.commit()
    
    flash(f'Company {company.name} has been unverified.', 'warning')
    return redirect(url_for('admin.companies'))

@bp.route('/companies/<int:company_id>/change-subscription-status', methods=['POST','GET'])
@admin_required
def change_subscription_status(company_id):
    """Change company plan"""
    company = Company.query.get_or_404(company_id)
    new_sub_status = request.form.get('sub_plan')
    
    sub_plan=SubscriptionPlan.query.filter_by(id=company.subscription_plan_id).first()
    sub_pay=SubscriptionPayment.query.filter_by(company_id=company_id).order_by(desc(SubscriptionPayment.id)).first()
    print(new_sub_status)
    print(sub_plan)
    
    company.subscription_status= "active"
    company.subscription_started_at=datetime.utcnow()
    company.subscription_ends_at=datetime.utcnow() + timedelta(days=365 if sub_pay.interval == 'yearly' else 30)
    company.max_active_listings=sub_plan.max_active_listings
    company.max_featured_listings=sub_plan.max_featured_listings
    company.max_team_members=sub_plan.max_team_members
    company.max_monthly_transactions=sub_plan.max_monthly_transactions
    company.commission_rate=sub_plan.commission_rate
    company.grace_period=False
    company.subscription_grace_period_ends=None
    sub_pay.status="active"
    db.session.commit()
    flash(f'Subscription plan  changed to {sub_plan.name}.', 'success')
    
    return redirect(url_for('admin.company_subscription',company_id=company.id))



# ============================================
# SUBSCRIPTION DASHBOARD
# ============================================

@bp.route('/subscriptions')
@login_required
def subscriptions():
    """Admin subscription management dashboard"""
    
    # Stats
    total_companies = Company.query.count()
    active_subscriptions = Company.query.filter_by(subscription_status='active').count()
    free_companies = Company.query.filter_by(subscription_status='free').count()
    grace_period = Company.query.filter_by(subscription_status='grace_period').count()
    expired = Company.query.filter_by(subscription_status='expired').count()
    
    # Revenue stats
    monthly_revenue = db.session.query(func.sum(SubscriptionPayment.amount)).filter(
        SubscriptionPayment.status == 'succeeded',
        SubscriptionPayment.paid_at >= datetime.utcnow() - timedelta(days=30)
    ).scalar() or 0
    
    total_revenue = db.session.query(func.sum(SubscriptionPayment.amount)).filter(
        SubscriptionPayment.status == 'succeeded'
    ).scalar() or 0
    
    # Recent payments
    recent_payments = SubscriptionPayment.query.order_by(
        desc(SubscriptionPayment.paid_at)
    ).limit(10).all()
    
    # Company subscriptions
    companies = Company.query.order_by(Company.created_at.desc()).limit(20).all()
    
    return render_template('subscriptions.html',
                         total_companies=total_companies,
                         active_subscriptions=active_subscriptions,
                         free_companies=free_companies,
                         grace_period=grace_period,
                         expired=expired,
                         monthly_revenue=monthly_revenue,
                         total_revenue=total_revenue,
                         recent_payments=recent_payments,
                         companies=companies)


# ============================================
# SUBSCRIPTION PLANS
# ============================================

@bp.route('/subscription/plans')
@login_required
def subscription_plans():
    """Manage subscription plans"""
    
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.sort_order).all()
    return render_template('subscription_plans.html', plans=plans)


@bp.route('/subscription/plans/add', methods=['GET', 'POST'])
@login_required
def add_subscription_plan():
    """Add a new subscription plan"""
    
    form = SubscriptionPlanForm()
    
    if form.validate_on_submit():
        try:
            plan = SubscriptionPlan(
                name=form.name.data,
                slug=form.slug.data or form.name.data.lower().replace(' ', '-'),
                description=form.description.data,
                price_monthly=form.price_monthly.data or 0,
                price_yearly=form.price_yearly.data or 0,
                currency=form.currency.data,
                max_active_listings=form.max_active_listings.data or 0,
                max_featured_listings=form.max_featured_listings.data or 0,
                max_team_members=form.max_team_members.data or 1,
                max_monthly_transactions=form.max_monthly_transactions.data or 0,
                commission_rate=form.commission_rate.data or 5.0,
                has_analytics=form.has_analytics.data,
                has_api_access=form.has_api_access.data,
                has_priority_support=form.has_priority_support.data,
                has_bulk_upload=form.has_bulk_upload.data,
                has_advanced_filters=form.has_advanced_filters.data,
                has_dedicated_manager=form.has_dedicated_manager.data,
                sort_order=form.sort_order.data or 0,
                is_active=form.is_active.data,
                is_popular=form.is_popular.data
            )
            
            db.session.add(plan)
            db.session.commit()
            
            flash(f'Plan "{plan.name}" created successfully!', 'success')
            return redirect(url_for('admin.subscription_plans'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating plan: {str(e)}', 'danger')
    
    return render_template('subscription_plan_form.html',
                         form=form,
                         title='Add Subscription Plan',
                         plan=None)


@bp.route('/subscription/plans/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_subscription_plan(plan_id):
    """Edit a subscription plan"""
    
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    form = SubscriptionPlanForm(obj=plan)
    
    if form.validate_on_submit():
        try:
            plan.name = form.name.data
            plan.slug = form.slug.data or form.name.data.lower().replace(' ', '-')
            plan.description = form.description.data
            plan.price_monthly = form.price_monthly.data or 0
            plan.price_yearly = form.price_yearly.data or 0
            plan.currency = form.currency.data
            plan.max_active_listings = form.max_active_listings.data or 0
            plan.max_featured_listings = form.max_featured_listings.data or 0
            plan.max_team_members = form.max_team_members.data or 1
            plan.max_monthly_transactions = form.max_monthly_transactions.data or 0
            plan.commission_rate = form.commission_rate.data or 5.0
            plan.has_analytics = form.has_analytics.data
            plan.has_api_access = form.has_api_access.data
            plan.has_priority_support = form.has_priority_support.data
            plan.has_bulk_upload = form.has_bulk_upload.data
            plan.has_advanced_filters = form.has_advanced_filters.data
            plan.has_dedicated_manager = form.has_dedicated_manager.data
            plan.sort_order = form.sort_order.data or 0
            plan.is_active = form.is_active.data
            plan.is_popular = form.is_popular.data
            plan.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Plan "{plan.name}" updated successfully!', 'success')
            return redirect(url_for('admin.subscription_plans'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating plan: {str(e)}', 'danger')
    
    return render_template('subscription_plan_form.html',
                         form=form,
                         title='Edit Subscription Plan',
                         plan=plan)


@bp.route('/subscription/plans/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_subscription_plan(plan_id):
    """Delete a subscription plan"""
    
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # Check if plan is in use
    if plan.companies.count() > 0:
        flash('Cannot delete plan with active subscribers.', 'danger')
        return redirect(url_for('admin.subscription_plans'))
    
    try:
        db.session.delete(plan)
        db.session.commit()
        flash(f'Plan "{plan.name}" deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting plan: {str(e)}', 'danger')
    
    return redirect(url_for('admin.subscription_plans'))


@bp.route('/subscription/plans/<int:plan_id>/toggle', methods=['POST'])
@login_required
def toggle_subscription_plan(plan_id):
    """Toggle plan active status"""
    
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    plan.is_active = not plan.is_active
    db.session.commit()
    
    status = 'activated' if plan.is_active else 'deactivated'
    flash(f'Plan "{plan.name}" {status}.', 'success')
    
    return redirect(url_for('admin.subscription_plans'))


# ============================================
# COMPANY SUBSCRIPTION MANAGEMENT
# ============================================

@bp.route('/subscription/company/<int:company_id>')
@login_required
def company_subscription(company_id):
    """View and manage a company's subscription"""
    
    company = Company.query.get_or_404(company_id)
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    payments = SubscriptionPayment.query.filter_by(
        company_id=company_id
    ).order_by(desc(SubscriptionPayment.paid_at)).all()
    
    return render_template('subscription_detail.html',
                         company=company,
                         plans=plans,
                         payments=payments)


@bp.route('/subscription/company/<int:company_id>/assign', methods=['POST'])
@login_required
def assign_subscription(company_id):
    """Assign a subscription plan to a company"""
    
    company = Company.query.get_or_404(company_id)
    plan_id = request.form.get('plan_id', type=int)
    interval = request.form.get('interval', 'monthly')
    duration_months = request.form.get('duration_months', type=int, default=1)
    
    plan = SubscriptionPlan.query.get(plan_id)
    if not plan:
        flash('Invalid subscription plan.', 'danger')
        return redirect(url_for('admin.company_subscription', company_id=company_id))
    
    try:
        # Calculate pricing
        if interval == 'yearly':
            price = plan.price_yearly
            end_date = datetime.utcnow() + timedelta(days=365)
        else:
            price = plan.price_monthly
            end_date = datetime.utcnow() + timedelta(days=30 * duration_months)
        
        # Update company
        company.subscription_plan_id = plan.id
        company.subscription_status = 'active'
        company.subscription_started_at = datetime.utcnow()
        company.subscription_ends_at = end_date
        company.max_active_listings = plan.max_active_listings
        company.max_featured_listings = plan.max_featured_listings
        company.max_team_members = plan.max_team_members
        company.max_monthly_transactions = plan.max_monthly_transactions
        company.commission_rate = plan.commission_rate
        
        # Create payment record (admin assigned)
        payment = SubscriptionPayment(
            company_id=company.id,
            subscription_plan_id=plan.id,
            amount=price,
            currency='DA',
            interval=interval,
            period_start=datetime.utcnow(),
            period_end=end_date,
            status='succeeded',
            payment_method='admin_assigned',
            notes=f'Assigned by admin {current_user.email}'
        )
        payment.generate_invoice_number()
        
        db.session.add(payment)
        db.session.commit()
        
        flash(f'Subscription "{plan.name}" assigned to {company.name} successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error assigning subscription: {str(e)}', 'danger')
    
    return redirect(url_for('admin.company_subscription', company_id=company_id))


@bp.route('/subscription/company/<int:company_id>/downgrade', methods=['POST'])
@login_required
def downgrade_company(company_id):
    """Downgrade company to free plan"""
    
    company = Company.query.get_or_404(company_id)
    reason = request.form.get('reason', '')
    
    try:
        free_plan = SubscriptionPlan.query.filter_by(slug='free').first()
        
        if free_plan:
            company.subscription_plan_id = free_plan.id
            company.max_active_listings = free_plan.max_active_listings
            company.max_featured_listings = free_plan.max_featured_listings
            company.max_team_members = free_plan.max_team_members
            company.max_monthly_transactions = free_plan.max_monthly_transactions
            company.commission_rate = free_plan.commission_rate
        
        company.subscription_status = 'expired'
        company.subscription_ends_at = datetime.utcnow()
        company.subscription_notes = reason
        
        db.session.commit()
        
        flash(f'Company "{company.name}" downgraded to Free plan.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error downgrading company: {str(e)}', 'danger')
    
    return redirect(url_for('admin.company_subscription', company_id=company_id))


@bp.route('/subscription/company/<int:company_id>/extend', methods=['POST'])
@login_required
def extend_subscription(company_id):
    """Extend a company's subscription"""
    
    company = Company.query.get_or_404(company_id)
    extend_months = request.form.get('extend_months', type=int, default=1)
    
    if not company.subscription_ends_at:
        flash('Company has no active subscription to extend.', 'danger')
        return redirect(url_for('admin.company_subscription', company_id=company_id))
    
    try:
        company.subscription_ends_at += timedelta(days=30 * extend_months)
        company.subscription_status = 'active'
        
        db.session.commit()
        
        flash(f'Subscription extended by {extend_months} months.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error extending subscription: {str(e)}', 'danger')
    
    return redirect(url_for('admin.company_subscription', company_id=company_id))


# ============================================
# LISTINGS MODERATION
# ============================================

@bp.route('/listings')
@admin_required
def listings():
    """Manage all listings"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    moderation = request.args.get('moderation', '')
    
    query = Item.query
    pending_count=query.filter_by(status="pending").count()
    if status:
        query = query.filter_by(status=status)
    

    
    pagination = query.order_by(desc(Item.created_at)).paginate(page=page, per_page=per_page)
    listings = pagination.items
    
    return render_template('listings.html', listings=listings, pagination=pagination,
                         status=status, moderation=moderation,pending_count=pending_count)


@bp.route('/listings/<int:listing_id>/moderate', methods=['POST'])
@admin_required
def moderate_listing(listing_id):
    """Moderate a listing (approve/reject/flag)"""
    listing = Item.query.get_or_404(listing_id)
    action = request.form.get('action')
    notes = request.form.get('notes')
    
    if action == 'approve':
       
        listing.status = 'active'
        flash('Listing approved and published.', 'success')
    elif action == 'reject':
      
        listing.status = 'rejected'
        flash('Listing rejected.', 'warning')
    elif action == 'flag':
        listing.status = 'flagged'
        flash('Listing flagged for review.', 'info')
    
    listing.moderation_notes = notes
    listing.moderated_at = datetime.utcnow()
    listing.moderated_by = current_user.id
    db.session.commit()
    
    return redirect(url_for('admin.listings'))


@bp.route('/listings/<int:listing_id>/delete', methods=['POST'])
@admin_required
def delete_listing(listing_id):
    """Delete a listing"""
    listing = Item.query.get_or_404(listing_id)
    db.session.delete(listing)
    db.session.commit()
    
    flash('Listing deleted.', 'success')
    return redirect(url_for('admin.listings'))


# ============================================
# TRANSACTIONS MANAGEMENT
# ============================================

@bp.route('/transactions')
@admin_required
def transactions():
    """Manage all transactions"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    
    query = Transaction.query
    
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(desc(Transaction.created_at)).paginate(page=page, per_page=per_page)
    transactions = pagination.items
    
    return render_template('transactions.html', transactions=transactions, pagination=pagination, status=status)


@bp.route('/transactions/<int:transaction_id>')
@admin_required
def transaction_detail(transaction_id):
    """View transaction details"""
    transaction = Transaction.query.get_or_404(transaction_id)
    return render_template('transactions_detail.html', transaction=transaction)


@bp.route('/transactions/<int:transaction_id>/resolve-dispute', methods=['POST'])
@admin_required
def resolve_dispute(transaction_id):
    """Resolve a disputed transaction"""
    transaction = Transaction.query.get_or_404(transaction_id)
    resolution = request.form.get('resolution')
    notes = request.form.get('notes')
    
    if resolution == 'release_to_seller':
        transaction.status = 'completed'
        transaction.completed_at = datetime.utcnow()
        flash('Funds released to seller.', 'success')
    elif resolution == 'refund_buyer':
        transaction.status = 'cancelled'
        transaction.cancelled_reason = notes
        flash('Buyer refunded.', 'success')
    
    transaction.dispute_resolved_at = datetime.utcnow()
    transaction.dispute_notes = notes
    db.session.commit()
    
    return redirect(url_for('admin.transaction_detail', transaction_id=transaction.id))


# ============================================
# CATEGORIES MANAGEMENT
# ============================================


# ============================================
# CATEGORIES LIST
# ============================================

@bp.route('/categories')
@login_required
def categories():
    """List all categories with their attributes"""
    
    # Get all categories with ordering
    categories = Category.query.order_by(Category.parent_id, Category.sort_order).all()
    
    # Get stats
    total_categories = Category.query.count()
    active_categories = Category.query.filter_by(is_active=True).count()
    total_attributes = Quality_attributes.query.count() 
    
    return render_template('categories.html',
                         categories=categories,
                         total_categories=total_categories,
                         active_categories=active_categories,
                         total_attributes=total_attributes)


# ============================================
# CREATE CATEGORY
# ============================================

@bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
def create_category():
    """Create a new category"""
    
    form = CategoryForm()
    
    # Populate parent category choices
    #form.parent_id.choices = [(0, 'None (Top Level)')] + [
    #    (c.id, c.name) for c in Category.query.filter_by(is_active=True).order_by(Category.name).all()
    #]
    
    if form.validate_on_submit():
        try:
            category = Category(
                name=form.name.data,
                slug=form.slug.data or form.name.data.lower().replace(' ', '-'),
                description=form.description.data,
                icon=form.icon.data,
                color=form.color.data,
                waste_type=form.waste_type.data,
                requires_license=form.requires_license.data,
                requires_special_handling=form.requires_special_handling.data,
                min_quantity_default=form.min_quantity_default.data or 0,
                sort_order=form.sort_order.data or 0,
                is_active=form.is_active.data,
                is_featured=form.is_featured.data,
                meta_title=form.meta_title.data,
                meta_description=form.meta_description.data
            )
            
            # Set parent (if selected)
            #if form.parent_id.data and form.parent_id.data != 0:
             #   category.parent_id = form.parent_id.data
            
            db.session.add(category)
            db.session.commit()
            
            flash(f'Category "{category.name}" created successfully!', 'success')
            return redirect(url_for('admin.categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating category: {str(e)}', 'danger')
    
    return render_template('category_form.html', 
                         form=form, 
                         title='Create Category',
                         category=None)


# ============================================
# EDIT CATEGORY
# ============================================

@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """Edit an existing category"""
    
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
   

    
    if form.validate_on_submit():
        print('++++++++++++++++++++++')
        try:
            print('----------------------')
            print(form.sort_order.data)
            category.name = form.name.data
            category.slug = form.slug.data or form.name.data.lower().replace(' ', '-')
            category.description = form.description.data
            category.icon = form.icon.data
            category.color = form.color.data
            category.waste_type = form.waste_type.data
            category.requires_license = form.requires_license.data
            category.requires_special_handling = form.requires_special_handling.data
            category.min_quantity_default = form.min_quantity_default.data or 0
            category.sort_order = form.sort_order.data or 0
            category.is_active = form.is_active.data
            category.is_featured = form.is_featured.data
            category.meta_title = form.meta_title.data
            category.meta_description = form.meta_description.data
            category.updated_at = datetime.utcnow()
            
            # Update parent
            #if form.parent_id.data and form.parent_id.data != 0:
            #    category.parent_id = form.parent_id.data
            #else:
            #    category.parent_id = None
            
            db.session.commit()
            
            flash(f'Category "{category.name}" updated successfully!', 'success')
            return redirect(url_for('admin.categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating category: {str(e)}', 'danger')
    
    return render_template('category_form.html', 
                         form=form, 
                         title='Edit Category',
                         category=category)


# ============================================
# DELETE CATEGORY
# ============================================

@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """Delete a category (admin only)"""
    
    category = Category.query.get_or_404(category_id)
    
    # Check if category has listings
    if len(category.items) > 0:
        flash('Cannot delete category with active listings. Reassign or delete listings first.', 'danger')
        return redirect(url_for('admin.categories'))
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{category.name}" deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'danger')
    
    return redirect(url_for('admin.categories'))


# ============================================
# TOGGLE CATEGORY STATUS
# ============================================

@bp.route('/categories/<int:category_id>/toggle-status', methods=['POST'])
@login_required
def toggle_category_status(category_id):
    """Toggle category active status"""
    
    category = Category.query.get_or_404(category_id)
    category.is_active = not category.is_active
    db.session.commit()
    
    status = 'activated' if category.is_active else 'deactivated'
    flash(f'Category "{category.name}" {status}.', 'success')
    
    return redirect(url_for('admin.categories'))


# ============================================
# MANAGE CATEGORY ATTRIBUTES
# ============================================

@bp.route('/categories/<int:category_id>/attributes')
@login_required
def category_attributes(category_id):
    """Manage quality attributes for a category"""
    
    category = Category.query.get_or_404(category_id)
    attributes = Quality_attributes.query.filter_by(
        category_id=category_id
    ).order_by(Quality_attributes.sort_order).all()
    
    return render_template('category_attributes.html',
                         category=category,
                         attributes=attributes)


# ============================================
# ADD CATEGORY ATTRIBUTE
# ============================================

@bp.route('/categories/<int:category_id>/attributes/add', methods=['GET', 'POST'])
@login_required
def add_category_attribute(category_id):
    """Add a quality attribute to a category"""
    
    category = Category.query.get_or_404(category_id)
    form = CategoryAttributeForm()
    
    if form.validate_on_submit():
        try:
            attribute = Quality_attributes(
                category_id=category.id,
                name=form.name.data,
                attribute_type=form.attribute_type.data,
                is_required=form.is_required.data,
                placeholder=form.placeholder.data,
                help_text=form.help_text.data,
                sort_order=form.sort_order.data or 0,
                is_active=form.is_active.data
            )
            
            db.session.add(attribute)
            db.session.flush()
            
            # Add options for select/radio/checkbox types
            if form.attribute_type.data in ['select', 'radio', 'checkbox']:
                options_text = request.form.get('options_text', '')
                if options_text:
                    option_values = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
                    for i, value in enumerate(option_values):
                        option = Quality_attribute_options(
                            attribute_id=attribute.id,
                            value=value,
                            sort_order=i
                        )
                        db.session.add(option)
            
            db.session.commit()
            
            flash(f'Attribute "{attribute.name}" added successfully!', 'success')
            return redirect(url_for('admin.category_attributes', category_id=category.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding attribute: {str(e)}', 'danger')
    
    return render_template('attribute_form.html',
                         form=form,
                         category=category,
                         title='Add Attribute')


# ============================================
# EDIT CATEGORY ATTRIBUTE
# ============================================

@bp.route('/attributes/<int:attribute_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category_attribute(attribute_id):
    """Edit a quality attribute"""
    
    attribute = Quality_attributes.query.get_or_404(attribute_id)
    category = attribute.owned_quality
    form = CategoryAttributeForm(obj=attribute)
    
    if form.validate_on_submit():
        try:
            attribute.name = form.name.data
            attribute.attribute_type = form.attribute_type.data
            attribute.is_required = form.is_required.data
            attribute.placeholder = form.placeholder.data
            attribute.help_text = form.help_text.data
            attribute.sort_order = form.sort_order.data or 0
            attribute.is_active = form.is_active.data
            attribute.updated_at = datetime.utcnow()
            
            # Update options if type changed
            if form.attribute_type.data in ['select', 'radio', 'checkbox']:
                # Clear existing options
                Quality_attribute_options.query.filter_by(attribute_id=attribute.id).delete()
                
                # Add new options
                options_text = request.form.get('options_text', '')
                if options_text:
                    option_values = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
                    for i, value in enumerate(option_values):
                        option = Quality_attribute_options(
                            attribute_id=attribute.id,
                            value=value,
                            sort_order=i
                        )
                        db.session.add(option)
            
            db.session.commit()
            
            flash(f'Attribute "{attribute.name}" updated successfully!', 'success')
            return redirect(url_for('admin.category_attributes', category_id=category.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating attribute: {str(e)}', 'danger')
    
    return render_template('attribute_form.html',
                         form=form,
                         category=category,
                         attribute=attribute,
                         title='Edit Attribute')


# ============================================
# DELETE CATEGORY ATTRIBUTE
# ============================================

@bp.route('/attributes/<int:attribute_id>/delete', methods=['POST'])
@login_required
def delete_category_attribute(attribute_id):
    """Delete a quality attribute"""
    
    attribute = QualityAttribute.query.get_or_404(attribute_id)
    category_id = attribute.category_id
    
    try:
        db.session.delete(attribute)
        db.session.commit()
        flash(f'Attribute deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting attribute: {str(e)}', 'danger')
    
    return redirect(url_for('admin.category_attributes', category_id=category_id))

# ============================================
# REPORTS
# ============================================

@bp.route('/reports')
@admin_required
def reports():
    """Generate reports"""
    return render_template('admin/reports.html')


@bp.route('/reports/export-users')
@admin_required
def export_users():
    """Export users to CSV"""
    import csv
    from io import StringIO
    from flask import Response
    
    users = User.query.all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Email', 'Name', 'Company', 'Role', 'Created At', 'Status'])
    
    for user in users:
        writer.writerow([
            user.id,
            user.email,
            user.full_name,
            user.company.name if user.company else 'N/A',
            user.role,
            user.created_at.strftime('%Y-%m-%d'),
            'Active' if user.is_active else 'Inactive'
        ])
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=users_export.csv'}
    )


@bp.route('/reports/export-transactions')
@admin_required
def export_transactions():
    """Export transactions to CSV"""
    import csv
    from io import StringIO
    from flask import Response
    
    transactions = Transaction.query.all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Listing', 'Seller', 'Buyer', 'Amount', 'Status', 'Date'])
    
    for t in transactions:
        writer.writerow([
            t.id,
            t.listing.title if t.listing else 'N/A',
            t.seller_company.name if t.seller_company else 'N/A',
            t.buyer_company.name if t.buyer_company else 'N/A',
            t.price,
            t.status,
            t.created_at.strftime('%Y-%m-%d')
        ])
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=transactions_export.csv'}
    )


# ============================================
# SETTINGS
# ============================================

@bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Platform settings"""
    form = AdminSettingsForm()
    
    if form.validate_on_submit():
        # Save settings to database or config
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', form=form)

