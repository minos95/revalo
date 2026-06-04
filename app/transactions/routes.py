import os
from flask import Blueprint, render_template,request,redirect,url_for,flash
from app import db
from app.auth.models import Company, Notification, User
from app.listings.models import Category,Item, Quality_attributes
from app.services.notification_service import NotificationService
from app.transactions.forms import markInTransitForm
from app.transactions.models import Transaction


from flask_login import login_required,current_user
from sqlalchemy import desc,or_
from datetime import datetime
from app.transactions import bp


@bp.route("/")
def index():
    NotificationService.mark_as_read_by_type(current_user.id,"transaction")

    
    transactions=Transaction.query.filter(or_(Transaction.seller_company_id==current_user.id ,Transaction.buyer_company_id==current_user.company_id)).order_by(desc(Transaction.created_at)).all()
    
    return render_template('transactions_index.html',transactions=transactions)


@bp.route("/detail/<int:transaction_id>",methods=['POST','GET'])
def detail(transaction_id):
    transaction=Transaction.query.get_or_404(transaction_id)
    mark_in_transit_form=markInTransitForm()
    print('-----------------------')
    print(current_user.company_id)
    if mark_in_transit_form.validate_on_submit() :
        print('------------------------- mar_in_trasit')
        transaction.mark_in_transit()
        
    
    return render_template('transactions_detail.html',transaction=transaction,mark_in_transit_form=mark_in_transit_form,)

@bp.route("/confirm/<int:transaction_id>")
def confirm(transaction_id):
    transaction=Transaction.query.get_or_404(transaction_id)
    
    return render_template('transaction_confirm.html',transaction=transaction)

@bp.route("/confirm_payment/<int:transaction_id>",methods=["POST"])
def confirm_payment(transaction_id):
    transaction=Transaction.query.get_or_404(transaction_id)
     # Check permission - only seller can confirm payment
    if transaction.seller_company_id != current_user.company_id:
        flash('You do not have permission to confirm payment for this transaction.', 'danger')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    # Check if transaction is in correct state
    if transaction.status != 'payment_pending':
        flash(f'Cannot confirm payment. Transaction status is {transaction.status}.', 'warning')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    # Check if payment is already confirmed
    if transaction.payment_confirmed:
        flash('Payment has already been confirmed.', 'info')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    if request.method == 'POST':
        try:
            # Get payment details from form
            #payment_reference = request.form.get('payment_reference', '')
            #payment_notes = request.form.get('payment_notes', '')
            
            # Update transaction
            transaction.payment_confirmed = True
            transaction.payment_confirmed_at = datetime.utcnow()
            transaction.payment_confirmed_by = current_user.id
            #transaction.payment_reference = payment_reference
            #transaction.payment_notes = payment_notes
            transaction.status = 'pending'
            transaction.payment_confirmed=True
            transaction.payment_confirmed_by=current_user.id
            transaction.payment_confirmed_at=datetime.utcnow()
            
            
           
            # Update company statistics
            seller_company = transaction.seller_company
            if seller_company:
                seller_company.total_transactions = (seller_company.total_transactions or 0) + 1
                seller_company.total_revenue = (seller_company.total_revenue or 0) + transaction.seller_net_amount
            
            buyer_company = transaction.buyer_company
            if buyer_company:
                buyer_company.total_transactions = (buyer_company.total_transactions or 0) + 1
            
            db.session.commit()
            
            # Create notification for buyer
            notification = Notification(
                user_id=transaction.buyer_manager_id,
                type='payment_confirmed',
                title='Payment Confirmed!',
                message=f'Seller has confirmed payment for transaction #{transaction.id}. Transaction completed.',
                related_type='transaction',
                related_id=transaction.id
            )
            db.session.add(notification)
            
            # Create notification for seller (optional - they already know)
            notification2 = Notification(
                user_id=transaction.seller_manager_id,
                type='transaction_completed',
                title='Transaction Completed!',
                message=f'Transaction #{transaction.id} has been completed successfully.',
                related_type='transaction',
                related_id=transaction.id
            )
            db.session.add(notification2)
            
            db.session.commit()
            
            flash('Payment confirmed! Transaction completed successfully.', 'success')
            return redirect(url_for('transactions.detail', transaction_id=transaction.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error confirming payment: {str(e)}', 'danger')
            return redirect(url_for('transactions.detail', transaction_id=transaction.id))

@bp.route("/review/<int:transaction_id>")
def review(transaction_id):
    transaction=Transaction.query.get_or_404(transaction_id)
    
@bp.route("/mark_delivered/<int:transaction_id>")
def mark_delivered(transaction_id):
    transaction=Transaction.query.get_or_404(transaction_id)
    
@bp.route("/mark_picked_up/<int:transaction_id>")
def mark_picked_up(transaction_id):
    transaction=Transaction.query.get_or_404(transaction_id)
    
    