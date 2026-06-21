from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.auth.models import User
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import desc

from app.listings.models import Item as Listing
from app.subscription import bp
from app.subscription.forms import UpgradeForm, PaymentMethodForm, CancelForm
from app.subscription.services import SubscriptionService
from app.subscription.models import SubscriptionPlan, SubscriptionPayment
from app.auth.models import Company
from app import db




# ============================================
# PRICING PAGE
# ============================================

@bp.route('/pricing')
def pricing():
    """Display subscription plans"""
    
    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.sort_order).all()
    
    # Get current user's plan if logged in
    current_plan = 1
    if current_user.is_authenticated and current_user.owned_company.subscription_plan_id :
        current_plan = current_user.owned_company.subscription_plan_id
       
    return render_template('pricing.html',
                         plans=plans,
                         current_plan=current_plan)


# ============================================
# UPGRADE SUBSCRIPTION
# ============================================

@bp.route('/upgrade', methods=['GET', 'POST'])
@login_required
def upgrade():
    """Upgrade to a paid subscription plan"""
    
    company = current_user.owned_company
    form = UpgradeForm()
    
    # Get available plans (excluding current plan)
    plans = SubscriptionPlan.query.filter(
        SubscriptionPlan.is_active == True,
        SubscriptionPlan.price_monthly > 0,  # Paid plans only
        SubscriptionPlan.id>company.subscription_plan_id
    ).order_by(SubscriptionPlan.price_monthly).all()
    
    form.plan_id.choices = [(p.id, f"{p.name} - ${p.price_monthly}/month") for p in plans]
    
    if request.method == 'GET' and plans:
        # Default to lowest paid plan
        form.plan_id.data = plans[0].id if plans else None
    
    if form.validate_on_submit():
        plan_id = form.plan_id.data
        interval = form.interval.data
        payment_method = form.payment_method.data
        
        plan = SubscriptionPlan.query.get(plan_id)
        
        if not plan:
            flash('Invalid subscription plan selected.', 'danger')
            return redirect(url_for('subscription.upgrade'))
        
        # Check if already on this plan
        if company.subscription_plan_id == plan_id and company.subscription_status == 'active':
            flash('You are already on this plan.', 'info')
            return redirect(url_for('subscription.billing'))
        
        # Calculate pricing
        if interval == 'yearly':
            price = plan.price_yearly
        else:
            price = plan.price_monthly
        
        # Here you would integrate with Stripe/PayPal
        # For now, we'll create a manual payment record
        
        try:
            # Create payment record
            payment = SubscriptionPayment(
                company_id=company.id,
                subscription_plan_id=plan.id,
                amount=price,
                currency='DA',
                interval=interval,
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow() + timedelta(days=365 if interval == 'yearly' else 30),
                payment_method=payment_method,
                status='pending'
            )
            payment.generate_invoice_number()
            db.session.add(payment)
            
            # Update company subscription (pending until payment confirmed)
            company.subscription_plan_id = plan.id
            company.subscription_status="pending"
            
            db.session.commit()
            
            # Redirect to payment page
            #return redirect(url_for('subscription.process_payment', payment_id=payment.id))
            return redirect(url_for('subscription.pricing'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating subscription: {str(e)}', 'danger')
    
    return render_template('upgrade.html', form=form, plans=plans,company=company)


# ============================================
# PROCESS PAYMENT
# ============================================

@bp.route('/payment/<int:payment_id>')
@login_required
def process_payment(payment_id):
    """Process payment for subscription"""
    
    payment = SubscriptionPayment.query.get_or_404(payment_id)
    
    # Check permission
    if payment.company_id != current_user.company_id:
        flash('You do not have permission to view this payment.', 'danger')
        return redirect(url_for('subscription.pricing'))
    
    # Simulate payment processing (replace with actual gateway)
    # In production, integrate with Stripe/PayPal here
    
    # For demo purposes, auto-confirm
    payment.status = 'succeeded'
    payment.paid_at = datetime.utcnow()
    
    # Update company subscription
    company = payment.company
    company.subscription_status = 'active'
    company.subscription_started_at = payment.period_start
    company.subscription_ends_at = payment.period_end
    company.max_active_listings = payment.subscription_plan.max_active_listings
    company.max_featured_listings = payment.subscription_plan.max_featured_listings
    company.max_team_members = payment.subscription_plan.max_team_members
    company.max_monthly_transactions = payment.subscription_plan.max_monthly_transactions
    company.commission_rate = payment.subscription_plan.commission_rate
    company.last_payment_date = datetime.utcnow()
    company.last_payment_amount = payment.amount
    company.last_invoice_url = payment.invoice_url
    
    db.session.commit()
    
    flash('Payment successful! Your subscription is now active.', 'success')
    return redirect(url_for('subscription.billing'))


# ============================================
# BILLING HISTORY
# ============================================

@bp.route('/billing')
@login_required
def billing():
    """View billing history and current subscription"""
    
    company = current_user.owned_company
    
    # Get current subscription
    current_plan = company.subscription_plan
    current_payment = SubscriptionPayment.query.filter_by(
        company_id=company.id,
        status='succeeded'
    ).order_by(desc(SubscriptionPayment.created_at)).first()
    
    # Get payment history
    payments = SubscriptionPayment.query.filter_by(
        company_id=company.id
    ).order_by(desc(SubscriptionPayment.created_at)).all()
    
    # Get upcoming invoice (next billing date)
    upcoming_invoice = None
    if company.subscription_status == 'active' and company.subscription_ends_at:
        if company.auto_renew:
            upcoming_invoice = {
                'date': company.subscription_ends_at,
                'amount': current_payment.amount if current_payment else 0
            }
    
    return render_template('billing.html',
                         company=company,
                         current_plan=current_plan,
                         current_payment=current_payment,
                         payments=payments,
                         upcoming_invoice=upcoming_invoice)


# ============================================
# CANCEL SUBSCRIPTION
# ============================================

@bp.route('/cancel', methods=['GET', 'POST'])
@login_required
def cancel():
    """Cancel subscription"""
    
    company = current_user.company
    form = CancelForm()
    
    if company.subscription_status != 'active':
        flash('You do not have an active subscription.', 'warning')
        return redirect(url_for('subscription.billing'))
    
    if form.validate_on_submit():
        reason = form.reason.data
        cancel_immediately = form.cancel_immediately.data
        
        if cancel_immediately:
            # Cancel immediately and downgrade to free
            company.subscription_status = 'cancelled'
            company.subscription_cancelled_at = datetime.utcnow()
            
            # Downgrade to free plan
            free_plan = SubscriptionPlan.query.filter_by(slug='free').first()
            if free_plan:
                company.subscription_plan_id = free_plan.id
                company.max_active_listings = free_plan.max_active_listings
                company.max_featured_listings = free_plan.max_featured_listings
                company.max_team_members = free_plan.max_team_members
                company.max_monthly_transactions = free_plan.max_monthly_transactions
                company.commission_rate = free_plan.commission_rate
            
            company.subscription_ends_at = datetime.utcnow()
            message = 'Your subscription has been cancelled immediately.'
        else:
            # Cancel at end of period
            company.auto_renew = False
            company.subscription_status = 'cancelling'
            company.subscription_cancelled_at = datetime.utcnow()
            message = 'Your subscription will be cancelled at the end of the billing period.'
        
        # Store cancellation reason
        company.subscription_notes = reason
        
        db.session.commit()
        
        flash(message, 'success')
        return redirect(url_for('subscription.billing'))
    
    # Calculate end date display
    end_date = company.subscription_ends_at
    days_left = (end_date - datetime.utcnow()).days if end_date else 0
    
    return render_template('subscription/cancel.html', 
                         form=form, 
                         company=company,
                         days_left=days_left)


# ============================================
# UPDATE PAYMENT METHOD
# ============================================

@bp.route('/payment-method', methods=['GET', 'POST'])
@login_required
def payment_method():
    """Update payment method"""
    
    company = current_user.company
    form = PaymentMethodForm()
    
    if form.validate_on_submit():
        # In production, integrate with Stripe/PayPal here
        company.default_payment_method = form.payment_method.data
        company.card_last4 = form.card_last4.data
        company.card_brand = form.card_brand.data
        company.card_expiry = f"{form.card_expiry_month.data}/{form.card_expiry_year.data}"
        
        db.session.commit()
        
        flash('Payment method updated successfully.', 'success')
        return redirect(url_for('subscription.billing'))
    
    # Pre-fill existing data
    if company.card_last4:
        form.card_last4.data = company.card_last4
        form.card_brand.data = company.card_brand
    
    return render_template('subscription/payment_method.html', form=form, company=company)


# ============================================
# INVOICES
# ============================================

@bp.route('/invoices')
@login_required
def invoices():
    """View all invoices"""
    
    payments = SubscriptionPayment.query.filter_by(
        company_id=current_user.company_id
    ).order_by(desc(SubscriptionPayment.created_at)).all()
    
    return render_template('subscription/invoices.html', payments=payments)


@bp.route('/invoice/<int:payment_id>/download')
@login_required
def download_invoice(payment_id):
    """Download invoice PDF"""
    
    payment = SubscriptionPayment.query.get_or_404(payment_id)
    
    if payment.company_id != current_user.company_id:
        flash('You do not have permission to download this invoice.', 'danger')
        return redirect(url_for('subscription.invoices'))
    
    # In production, generate PDF invoice
    # For now, redirect to invoice URL or show HTML version
    
    if payment.invoice_url:
        return redirect(payment.invoice_url)
    
    # Generate simple HTML invoice
    return render_template('subscription/invoice_pdf.html', payment=payment)


# ============================================
# API - GET CURRENT PLAN
# ============================================

@bp.route('/api/current-plan')
@login_required
def api_current_plan():
    """Get current subscription plan details (for frontend)"""
    
    company = current_user.company
    
    return jsonify({
        'plan_name': company.subscription_plan.name if company.subscription_plan else 'Free',
        'plan_slug': company.subscription_plan.slug if company.subscription_plan else 'free',
        'status': company.subscription_status,
        'ends_at': company.subscription_ends_at.isoformat() if company.subscription_ends_at else None,
        'max_active_listings': company.max_active_listings,
        'max_team_members': company.max_team_members,
        'used_listings': Listing.query.filter_by(company_id=company.id, status='active').count(),
        'used_team_members': User.query.filter_by(company_id=company.id).count(),
        'commission_rate': float(company.commission_rate)
    })


# ============================================
# API - USAGE STATS
# ============================================

@bp.route('/api/usage')
@login_required
def api_usage():
    """Get current usage statistics"""
    
    company = current_user.company
    
    active_listings = Listing.query.filter_by(company_id=company.id, status='active').count()
    team_members = User.query.filter_by(company_id=company.id).count()
    
    return jsonify({
        'listings': {
            'used': active_listings,
            'limit': company.max_active_listings,
            'percentage': round((active_listings / company.max_active_listings) * 100) if company.max_active_listings > 0 else 0
        },
        'team': {
            'used': team_members,
            'limit': company.max_team_members,
            'percentage': round((team_members / company.max_team_members) * 100) if company.max_team_members > 0 else 0
        }
    })