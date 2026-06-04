from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.admin import bp
from app.admin.forms import AdminSettingsForm, CategoryForm, ModerationForm
from app.auth.models import User, Company
from app.listings.models import Item,Category
from app.transactions.models import Transaction
from app.offers.models import Offer
from app.subscription.models import SubscriptionPlan
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
    total_revenue = db.session.query(func.sum(Transaction.price)).filter(
        Transaction.status == 'completed'
    ).scalar() or 0
    
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
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
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
    db.session.commit()
    
    flash(f'Company {company.name} has been verified.', 'success')
    return redirect(url_for('admin.companies'))


@bp.route('/companies/<int:company_id>/unverify', methods=['POST'])
@admin_required
def unverify_company(company_id):
    """Unverify a company"""
    company = Company.query.get_or_404(company_id)
    company.verified = False
    db.session.commit()
    
    flash(f'Company {company.name} has been unverified.', 'warning')
    return redirect(url_for('admin.companies'))

@bp.route('/companies/<int:company_id>/change-subscription-status', methods=['POST'])
@admin_required
def change_subscription_status(company_id):
    """Change company plan"""
    company = Company.query.get_or_404(company_id)
    new_sub_status = request.form.get('sub_plan')
    
    sub_plan=SubscriptionPlan.query.filter_by(id=company.subscription_plan_id_temporary).first()
    print(new_sub_status)
    print(sub_plan)
    company.subscription_plan_id = sub_plan.id
    company.subscription_plan_id_temporary = None
    company.subscription_status= "active"
    company.subscription_started_at=datetime.utcnow()
    company.subscription_ends_at=datetime.utcnow() +timedelta(days=90)
    company.max_active_listings=sub_plan.max_active_listings
    company.max_featured_listings=sub_plan.max_featured_listings
    company.max_team_members=sub_plan.max_team_members
    company.max_monthly_transactions=sub_plan.max_monthly_transactions
    company.commission_rate=sub_plan.commission_rate
    db.session.commit()
    flash(f'Subscription plan  changed to {sub_plan.name}.', 'success')
    
    return redirect(url_for('admin.companies'))


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
    return render_template('admin/transaction_detail.html', transaction=transaction)


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

@bp.route('/categories')
@admin_required
def categories():
    """Manage categories"""
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)


@bp.route('/categories/create', methods=['GET', 'POST'])
@admin_required
def create_category():
    """Create a new category"""
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            slug=form.name.data.lower().replace(' ', '-'),
            description=form.description.data,
            icon=form.icon.data,
            parent_id=form.parent_id.data or None,
            sort_order=form.sort_order.data,
            is_active=form.is_active.data
        )
        db.session.add(category)
        db.session.commit()
        
        flash('Category created successfully!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('category_form.html', form=form, title='Create Category')


@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    """Edit a category"""
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.icon = form.icon.data
        category.parent_id = form.parent_id.data or None
        category.sort_order = form.sort_order.data
        category.is_active = form.is_active.data
        db.session.commit()
        
        flash('Category updated!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html', form=form, title='Edit Category', category=category)


@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@admin_required
def delete_category(category_id):
    """Delete a category"""
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted.', 'success')
    return redirect(url_for('admin.categories'))


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

