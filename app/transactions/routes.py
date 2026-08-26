import os
from urllib.parse import unquote
import app
from app.services.rating_service import RatingService
from app.services.transaction_service import TransactionService
from flask import Blueprint, abort, render_template,request,redirect, send_file,url_for,flash,current_app,send_from_directory
from app import db
from app.auth.models import Company, Notification, Review, User
from app.listings.models import Category,Item, Quality_attributes
from app.services.notification_service import NotificationService
from app.transactions.forms import markInTransitForm
from app.transactions.models import Transaction


from flask_login import login_required,current_user
from sqlalchemy import desc,or_
from datetime import datetime
from app.transactions import bp
from werkzeug.utils import secure_filename

@bp.route("/")
@login_required
def index():
    NotificationService.mark_as_read_by_type(current_user.id,"transaction")

    
    transactions=Transaction.query.filter(or_(Transaction.seller_company_id==current_user.id ,Transaction.buyer_company_id==current_user.company_id)).order_by(desc(Transaction.created_at)).all()
    
    return render_template('transactions_index.html',transactions=transactions)


@bp.route("/detail/<int:transaction_id>",methods=['POST','GET'])
@login_required
def detail(transaction_id):
    transaction=Transaction.query.get_or_404(transaction_id)
    mark_in_transit_form=markInTransitForm()
    print('-----------------------')
    print(current_user.company_id)
    if mark_in_transit_form.validate_on_submit() :
        print('------------------------- mar_in_trasit')
        transaction.mark_in_transit()
        
    
    return render_template('transactions_detail.html',transaction=transaction,mark_in_transit_form=mark_in_transit_form,)




# app/transactions/routes.py

@bp.route('/<int:transaction_id>/pay', methods=['GET', 'POST'])
@login_required
def process_payment(transaction_id):
    """Process payment for transaction"""
    
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Check if user is buyer
    if transaction.buyer_company_id != current_user.company_id:
        flash('You are not authorized to pay for this transaction.', 'danger')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    # Check if payment already processed
    if transaction.payment_status == 'paid':
        flash('Payment already processed.', 'info')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    if request.method == 'POST':
        # Process payment (Stripe/PayPal/etc)
        # For demo, simulate payment
        file=request.files['payment_url']   
        transaction.payment_status = 'paid'
        transaction.paid_at = datetime.utcnow()
        transaction.status = 'confirmed'
        transaction.confirmed_at = datetime.utcnow()
        
        
        if file and allowed_file(file.filename) :
                print('--------------------------- file')
                filename = secure_filename(f"payment_{transaction_id}_{current_user.id}_{file.filename}")
                file_path=os.path.join(current_app.config['UPLOAD_FOLDER'], f'transactions/{transaction_id}/payment', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path) 
                transaction.payment_url=filename    
        
        db.session.commit()
        
        # Notify seller
        notification = Notification(
                user_id=transaction.seller_manager_id,
                type='transaction_paid',
                title='Transaction paid!',
                message=f'Transaction #{transaction.id} has been paid please confirm you received it.',
                related_type='transaction',
                related_id=transaction.id
            )
        db.session.add(notification)
            
        db.session.commit()  
        
        flash('Payment successful! Seller has been notified.', 'success')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    return render_template('transactions_payment.html', transaction=transaction)

@bp.route("/confirm_payment/<int:transaction_id>",methods=["POST"])
def confirm_payment(transaction_id):
    transaction=Transaction.query.get_or_404(transaction_id)
     # Check permission - only seller can confirm payment
    if transaction.seller_company_id != current_user.company_id:
        flash('You do not have permission to confirm payment for this transaction.', 'danger')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    # Check if transaction is in correct state
    if transaction.status == 'confirmed':
        flash(f'Cannot confirm payment. Transaction payment status is {transaction.status}.', 'warning')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    # Check if payment is already confirmed
    if transaction.payment_confirmed:
        flash('Payment has already been confirmed.', 'info')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    if request.method == 'POST':
        print("+++++++++++++++++++++++++++++method post")
        try:
            # Get payment details from form
            #payment_reference = request.form.get('payment_reference', '')
            #payment_notes = request.form.get('payment_notes', '')
            
            # Update transaction
            transaction.payment_confirmed = True
            transaction.payment_confirmed_at = datetime.utcnow()
            transaction.payment_confirmed_by = current_user.id
            
            transaction.payment_confirmed_by=current_user.id
            transaction.payment_confirmed_at=datetime.utcnow()
            
            
           
            # Update company statistics
            """
            seller_company = transaction.seller_company
            if seller_company:
                seller_company.total_transactions = (seller_company.total_transactions or 0) + 1
                seller_company.total_revenue = (seller_company.total_revenue or 0) + transaction.seller_net_amount
            
            buyer_company = transaction.buyer_company
            if buyer_company:
                buyer_company.total_transactions = (buyer_company.total_transactions or 0) + 1
            """
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
        


@bp.route('/<int:transaction_id>/schedule-pickup', methods=['GET', 'POST'])
@login_required
def schedule_pickup(transaction_id):
    """Schedule pickup for the transaction"""
    
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Only seller can schedule
    if transaction.seller_company_id != current_user.company_id:
        flash('Only the seller can schedule pickup.', 'danger')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    if request.method == 'POST':
        pickup_datetime = request.form.get('pickup_datetime')
        pickup_address = request.form.get('pickup_address')
        notes = request.form.get('notes')
        
        transaction.pickup_scheduled_at = datetime.strptime(pickup_datetime, '%Y-%m-%dT%H:%M')
        transaction.pickup_address = pickup_address
        transaction.pickup_notes = notes
        
        
        
        # Notify buyer
      
        notification = Notification(
                user_id=transaction.buyer_manager_id,
                type='transaction_schedul_pickup',
                title='Transaction scheduled pickup!',
                message=f'Transaction #{transaction.id} pickup has been scheduled.',
                related_type='transaction',
                related_id=transaction.id
            )
        db.session.add(notification)
        
        db.session.commit()
        flash('Pickup scheduled successfully!', 'success')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    return render_template('transactions/schedule_pickup.html', transaction=transaction)

# app/transactions/routes.py

@bp.route('/<int:transaction_id>/confirm-pickup', methods=['POST'])
@login_required
def confirm_pickup(transaction_id):
    """Confirm that materials have been picked up"""
    
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Only seller can confirm pickup
    if transaction.seller_company_id != current_user.company_id:
        flash('Only the seller can confirm pickup.', 'danger')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    if request.method == 'POST':
        file=request.files['weight_certificate']  
    
        if file and allowed_file(file.filename) :
                    print('--------------------------- file')
                    filename = secure_filename(f"weight_certificate_{transaction_id}_{current_user.id}_{file.filename}")
                    file_path=os.path.join(current_app.config['UPLOAD_FOLDER'], f'transactions/{transaction_id}/weight_certificate', filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path) 
                    transaction.weight_certificate_url=filename    
        
        # Update status
        transaction.pickup_completed_at = datetime.utcnow()
        transaction.status = 'in_transit'
        transaction.in_transit_at = datetime.utcnow()
    
    
    
        # Notify buyer
        notification = Notification(
                    user_id=transaction.buyer_manager_id,
                    type='transaction_confirm_pickup',
                    title='Transaction confirmed pickup!',
                    message=f'Transaction #{transaction.id} pickup has been scheduled.',
                    related_type='transaction',
                    related_id=transaction.id
                )
        db.session.add(notification)

        db.session.commit()
    
    flash('Pickup confirmed! Materials are in transit.', 'success')
    return redirect(url_for('transactions.detail', transaction_id=transaction.id))

# app/transactions/routes.py

@bp.route('/<int:transaction_id>/confirm-delivery', methods=['POST'])
@login_required
def confirm_delivery(transaction_id):
    """
    Buyer confirms delivery of materials.
    Only the buyer can confirm delivery.
    """
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Check if user is the buyer
    if transaction.buyer_company_id != current_user.company_id:
        flash('Only the buyer can confirm delivery.', 'danger')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    # Check if transaction is in correct state
    if transaction.status != 'in_transit':
        flash(f'Cannot confirm delivery in {transaction.status} status.', 'warning')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    # Check if already confirmed
    if transaction.delivery_confirmed:
        flash('Delivery already confirmed.', 'info')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    if request.method == 'POST':
        try:
            quality_notes = request.form.get('quality_notes', '')
            
            # Update transaction
            transaction.delivery_confirmed = True
            transaction.delivery_confirmed_at = datetime.utcnow()
            transaction.delivery_confirmed_by = current_user.id
            transaction.status = 'delivered'
            transaction.delivered_at = datetime.utcnow()
            
            
            
            if quality_notes:
                transaction.quality_notes = quality_notes
            
            # Log transition
            TransactionService._log_transition(
                transaction,
                'delivered',
                f'Delivery confirmed by buyer: {quality_notes[:50] if quality_notes else "No issues"}'
            )
            
            db.session.commit()
            
            # Notify seller
            NotificationService.create_notification(
                user_id=transaction.seller_manager_id,
                notification_type='delivery_confirmed',
                title='Delivery Confirmed',
                message=f'Buyer has confirmed delivery of materials for transaction #{transaction.id}.',
                related_type='transaction',
                related_id=transaction.id,
                priority='high'
            )
            
            # Notify buyer (confirmation)
            NotificationService.create_notification(
                user_id=current_user.id,
                notification_type='delivery_confirmed',
                title='Delivery Confirmed',
                message=f'You have confirmed delivery for transaction #{transaction.id}.',
                related_type='transaction',
                related_id=transaction.id,
                priority='normal'
            )
            
            flash('Delivery confirmed successfully! Payment will be released to the seller.', 'success')
            
            # Check if seller should get payment automatically
            # This depends on your business logic
            # Option 1: Auto-release payment
            # Option 2: Wait for seller to confirm payment
            if transaction.payment_confirmed:
                print('---------------------------- transaction completed')
                TransactionService.complete_transaction(transaction.id)
              
            return redirect(url_for('transactions.detail', transaction_id=transaction.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error confirming delivery: {str(e)}', 'danger')
            return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    # GET request - show confirmation page
    return render_template('transactions/confirm_delivery.html', transaction=transaction)





@bp.route('/<int:transaction_id>/review', methods=['GET', 'POST'])
@login_required
def leave_review(transaction_id):
    """Leave a review for the transaction"""
    
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Check if transaction is completed
    if transaction.status != 'completed':
        flash('You can only review completed transactions.', 'warning')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    # Check if user is participant
    if transaction.seller_company_id != current_user.company_id and transaction.buyer_company_id != current_user.company_id:
        flash('You are not authorized to review this transaction.', 'danger')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment')
        
        # Determine reviewee
        is_seller = transaction.seller_company_id == current_user.company_id
        reviewee_id = transaction.buyer_company_id if is_seller else transaction.seller_company_id
        reviewer_type = 'seller' if is_seller else 'buyer'
        # Create review
        review = Review(
            company_id=reviewee_id,
            reviewer_id=current_user.id,
            reviewer_type=reviewer_type,
            transaction_id=transaction.id,
            listing_id=transaction.item_id,
            rating=rating,
            comment=comment
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Update company rating
        RatingService.update_company_rating(reviewee_id)
        
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('transactions.detail', transaction_id=transaction.id))
    
    return render_template('transactions/review.html', transaction=transaction)

# ============================================
# COMPLETE TRANSACTION ROUTE
# ============================================

@bp.route('/<int:transaction_id>/complete', methods=['POST'])
@login_required
def complete(transaction_id):
    """
    Seller completes the transaction after delivery.
    Releases payment and marks as complete.
    """
    try:
        payment_reference = request.form.get('payment_reference')
        
        transaction = TransactionService.complete_transaction(
            transaction_id=transaction_id,
            user_id=current_user.id,
            payment_reference=payment_reference
        )
        
        flash('Transaction completed successfully! Payment released.', 'success')
        
    except PermissionError as e:
        flash(str(e), 'danger')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error completing transaction: {str(e)}', 'danger')
    
    return redirect(url_for('transactions.detail', transaction_id=transaction_id))


# ============================================
# REPORT DISPUTE ROUTE
# ============================================

@bp.route('/<int:transaction_id>/report-dispute', methods=['POST'])
@login_required
def report_dispute(transaction_id):
    """
    Report a dispute for a transaction.
    Both buyer and seller can report.
    """
    issue_type = request.form.get('issue_type')
    description = request.form.get('description')
    
    if not issue_type or not description:
        flash('Please provide both issue type and description.', 'danger')
        return redirect(url_for('transactions.detail', transaction_id=transaction_id))
    
    # Handle evidence files (optional)
    evidence_files = []
    if 'evidence_files' in request.files:
        files = request.files.getlist('evidence_files')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(f"dispute_{transaction_id}_{current_user.id}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'disputes', filename))
                evidence_files.append(filename)
    
    try:
        transaction = TransactionService.report_dispute(
            transaction_id=transaction_id,
            user_id=current_user.id,
            issue_type=issue_type,
            description=description,
            evidence_files=evidence_files
        )
        
        flash('Dispute reported. Our team will review within 24 hours.', 'warning')
        
    except ValueError as e:
        flash(str(e), 'danger')
    except PermissionError as e:
        flash(str(e), 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error reporting dispute: {str(e)}', 'danger')
    
    return redirect(url_for('transactions.detail', transaction_id=transaction_id))


# ============================================
# RESOLVE DISPUTE (Admin Only)
# ============================================

@bp.route('/<int:transaction_id>/resolve-dispute', methods=['POST'])
@login_required
def resolve_dispute(transaction_id):
    """
    Admin resolves a dispute.
    Only accessible to admin users.
    """
    if current_user.role != 'admin':
        flash('Only administrators can resolve disputes.', 'danger')
        return redirect(url_for('transactions.detail', transaction_id=transaction_id))
    
    transaction = Transaction.query.get_or_404(transaction_id)
    
    if not transaction.is_disputed:
        flash('This transaction is not under dispute.', 'info')
        return redirect(url_for('transactions.detail', transaction_id=transaction_id))
    
    resolution = request.form.get('resolution')
    notes = request.form.get('notes')
    
    if resolution not in ['release_to_seller', 'refund_buyer', 'cancel']:
        flash('Invalid resolution.', 'danger')
        return redirect(url_for('transactions.detail', transaction_id=transaction_id))
    
    try:
        if resolution == 'release_to_seller':
            # Release payment to seller
            TransactionService.complete_transaction(
                transaction_id=transaction.id,
                user_id=current_user.id,
                payment_reference='Dispute resolution'
            )
            transaction.is_disputed = False
            transaction.dispute_status = 'resolved'
            transaction.dispute_resolution = 'released_to_seller'
            transaction.dispute_notes = notes
            flash('Dispute resolved: Payment released to seller.', 'success')
            
        elif resolution == 'refund_buyer':
            # Refund buyer
            transaction.status = 'cancelled'
            transaction.cancelled_reason = f'Dispute resolved: {notes}'
            transaction.is_disputed = False
            transaction.dispute_status = 'resolved'
            transaction.dispute_resolution = 'refunded_buyer'
            transaction.dispute_notes = notes
            # Refund logic would go here (Stripe/PayPal)
            flash('Dispute resolved: Buyer refunded.', 'success')
            
        elif resolution == 'cancel':
            # Cancel transaction entirely
            transaction.status = 'cancelled'
            transaction.cancelled_reason = f'Dispute resolved: {notes}'
            transaction.is_disputed = False
            transaction.dispute_status = 'resolved'
            transaction.dispute_resolution = 'cancelled'
            transaction.dispute_notes = notes
            flash('Dispute resolved: Transaction cancelled.', 'success')
        
        transaction.dispute_resolved_at = datetime.utcnow()
        transaction.dispute_resolved_by = current_user.id
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error resolving dispute: {str(e)}', 'danger')
    
    return redirect(url_for('transactions.detail', transaction_id=transaction_id))


# ============================================
# HELPER FUNCTION
# ============================================

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp'}


# ============================================
# CANCEL TRANSACTION ROUTE
# ============================================

@bp.route('/<int:transaction_id>/cancel', methods=['POST'])
@login_required
def cancel(transaction_id):
    """
    Cancel a transaction.
    Both buyer and seller can cancel before completion.
    """
    reason = request.form.get('reason')
    notes = request.form.get('notes')
    
    if not reason:
        flash('Please provide a reason for cancellation.', 'danger')
        return redirect(url_for('transactions.detail', transaction_id=transaction_id))
    
    try:
        transaction = TransactionService.cancel_transaction(
            transaction_id=transaction_id,
            user_id=current_user.id,
            reason=reason,
            notes=notes
        )
        
        flash('Transaction cancelled successfully.', 'warning')
        
    except ValueError as e:
        flash(str(e), 'danger')
    except PermissionError as e:
        flash(str(e), 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling transaction: {str(e)}', 'danger')
    
    return redirect(url_for('transactions.detail', transaction_id=transaction_id))

@bp.route('/uploads/<transaction_id>/<filename>')
def download_payment(filename,transaction_id):
     # 1. Build the absolute path
    directory = os.path.abspath(os.path.join(
        current_app.config['UPLOAD_FOLDER'], 
        'transactions', 
        str(transaction_id), 
        'payment'
    ))
    
    file_path = os.path.join(directory, filename)
    print(f"Full file path: {file_path}")
    print(f"File exists?: {os.path.exists(file_path)}")
    
    # 2. Check if the physical file exists before sending
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        abort(404)
        
    # 3. Serve the file directly
    return send_file(file_path, as_attachment=True)

@bp.route('/downloadweightcertificate/<transaction_id>/<filename>')
def download_weight_certificate(filename,transaction_id):
     # 1. Build the absolute path
    directory = os.path.abspath(os.path.join(
        current_app.config['UPLOAD_FOLDER'], 
        'transactions', 
        str(transaction_id), 
        'weight_certificate'
    ))
    
    file_path = os.path.join(directory, filename)
    print(f"Full file path: {file_path}")
    print(f"File exists?: {os.path.exists(file_path)}")
    
    # 2. Check if the physical file exists before sending
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        abort(404)
        
    # 3. Serve the file directly
    return send_file(file_path, as_attachment=True)