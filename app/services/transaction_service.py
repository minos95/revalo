# app/services/transaction_service.py

from datetime import datetime
from app.auth.models import User
from app.transactions.models import Transaction
from app import db
from app.services.notification_service import NotificationService
from flask_login import current_user

class TransactionService:
    """Service for managing transaction lifecycle"""
    
    @staticmethod
    def create_transaction(offer, listing, price, quantity):
        """Step 1: Create transaction from accepted offer"""
        
        transaction = Transaction(
            offer_id=offer.id,
            listing_id=listing.id,
            seller_company_id=listing.company_id,
            buyer_company_id=offer.company_id,
            final_price=price,
            quantity=quantity,
            status='pending',
            payment_status='pending',
            status_history=[
                {
                    'status': 'pending',
                    'timestamp': datetime.utcnow().isoformat(),
                    'note': 'Transaction created from accepted offer'
                }
            ]
        )
        
        db.session.add(transaction)
        db.session.flush()
        transaction.generate_invoice_number()
        db.session.commit()
        
        TransactionService._log_transition(
            transaction,
            'pending',
            'Transaction created'
        )
        
        return transaction
    
    @staticmethod
    def confirm_transaction(transaction_id, payment_reference=None):
        """Step 2: Confirm transaction after payment"""
        
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError('Transaction not found')
        
        transaction.status = 'confirmed'
        transaction.confirmed_at = datetime.utcnow()
        transaction.payment_status = 'paid'
        transaction.paid_at = datetime.utcnow()
        
        if payment_reference:
            transaction.payment_reference = payment_reference
        
        TransactionService._log_transition(
            transaction,
            'confirmed',
            f'Payment received (ref: {payment_reference})'
        )
        
        db.session.commit()
        return transaction
    
    @staticmethod
    def schedule_pickup(transaction_id, scheduled_at, address=None, notes=None):
        """Step 3: Schedule pickup"""
        
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError('Transaction not found')
        
        if transaction.status not in ['confirmed', 'pending']:
            raise ValueError(f'Cannot schedule pickup in {transaction.status} status')
        
        transaction.pickup_scheduled_at = scheduled_at
        if address:
            transaction.pickup_address = address
        if notes:
            transaction.pickup_notes = notes
        
        TransactionService._log_transition(
            transaction,
            'pickup_scheduled',
            f'Pickup scheduled for {scheduled_at.strftime("%Y-%m-%d %H:%M")}'
        )
        
        db.session.commit()
        return transaction
    
    @staticmethod
    def confirm_pickup(transaction_id, weight_certificate=None):
        """Step 4: Confirm pickup completed"""
        
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError('Transaction not found')
        
        if transaction.status != 'confirmed':
            raise ValueError(f'Cannot confirm pickup in {transaction.status} status')
        
        if not transaction.pickup_scheduled_at:
            raise ValueError('Pickup must be scheduled first')
        
        transaction.status = 'in_transit'
        transaction.in_transit_at = datetime.utcnow()
        transaction.pickup_completed_at = datetime.utcnow()
        
        if weight_certificate:
            transaction.weight_certificate_url = weight_certificate
        
        TransactionService._log_transition(
            transaction,
            'in_transit',
            'Pickup completed, materials in transit'
        )
        
        db.session.commit()
        return transaction
    
    @staticmethod
    def confirm_delivery(transaction_id, quality_notes=None):
        """Step 5: Confirm delivery completed"""
        
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError('Transaction not found')
        
        if transaction.status != 'in_transit':
            raise ValueError(f'Cannot confirm delivery in {transaction.status} status')
        
        transaction.status = 'delivered'
        transaction.delivered_at = datetime.utcnow()
        transaction.delivery_completed_at = datetime.utcnow()
        
        if quality_notes:
            transaction.quality_notes = quality_notes
        
        TransactionService._log_transition(
            transaction,
            'delivered',
            f'Delivery completed: {quality_notes or "No issues"}'
        )
        
        db.session.commit()
        return transaction
    
    @staticmethod
    def complete_transaction(transaction_id, payment_reference=None):
        """
        Complete transaction after delivery confirmation.
        Only seller can complete, releases payment.
        """
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError('Transaction not found')
        
        # Check status
        if transaction.status != 'delivered' :
            raise ValueError(f'Cannot complete transaction in {transaction.status} status')
        
        
        
        # Update transaction
        transaction.status = 'completed'
        transaction.completed_at = datetime.utcnow()
        #transaction.payment_status = 'released'
        #transaction.payment_released_at = datetime.utcnow()
        #transaction.payment_confirmed = True
        #transaction.payment_confirmed_at = datetime.utcnow()
        
        if payment_reference:
            transaction.payment_reference = payment_reference
        
        # Update company stats
        seller_company = transaction.seller_company
        seller_company.total_transactions = (seller_company.total_transactions or 0) + 1
        seller_company.total_revenue = (seller_company.total_revenue or 0) + (transaction.total_amount - transaction.commission_amount)
        
        buyer_company = transaction.buyer_company
        buyer_company.total_transactions = (buyer_company.total_transactions or 0) + 1
        
        # Log transition
        TransactionService._log_transition(
            transaction,
            'completed',
            'Transaction completed, payment released'
        )
        
        db.session.commit()
        
        # Notify buyer
        NotificationService.create_notification(
            user_id=transaction.buyer_manager_id,
            notification_type='transaction_completed',
            title='Transaction Complete!',
            message=f'Transaction #{transaction.id} has been completed successfully.',
            related_type='transaction',
            related_id=transaction.id,
            priority='high'
        )
        
        return transaction
    
    @staticmethod
    def report_dispute(transaction_id, user_id, issue_type, description, evidence_files=None):
        """
        Report a dispute for a transaction.
        Both parties can report.
        """
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError('Transaction not found')
        
        # Check if already disputed
        if transaction.is_disputed:
            raise ValueError('This transaction is already under dispute')
        
        # Check if transaction is eligible (not completed or cancelled)
        if transaction.status in ['completed', 'cancelled']:
            raise ValueError(f'Cannot dispute a {transaction.status} transaction')
        
        # Check permission (must be participant)
        is_seller = transaction.seller_company.users.filter_by(id=user_id).first() is not None
        is_buyer = transaction.buyer_company.users.filter_by(id=user_id).first() is not None
        if not (is_seller or is_buyer):
            raise PermissionError('You are not a party to this transaction')
        
        # Update transaction
        transaction.is_disputed = True
        transaction.dispute_status = 'pending'
        transaction.dispute_raised_by = user_id
        transaction.dispute_raised_at = datetime.utcnow()
        transaction.dispute_issue_type = issue_type
        transaction.dispute_description = description
        
        if evidence_files:
            transaction.dispute_evidence = evidence_files  # JSON list of file URLs
        
        # Log transition
        TransactionService._log_transition(
            transaction,
            'disputed',
            f'Dispute raised: {issue_type}'
        )
        
        db.session.commit()
        
        # Notify admin
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            NotificationService.create_notification(
                user_id=admin.id,
                notification_type='dispute_reported',
                title='New Dispute Reported',
                message=f'Transaction #{transaction.id} has been disputed by {transaction.dispute_raised_by_user.full_name}.',
                related_type='transaction',
                related_id=transaction.id,
                priority='urgent'
            )
        
        return transaction
    
    @staticmethod
    def cancel_transaction(transaction_id, reason):
        """Cancel transaction (any step)"""
        
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError('Transaction not found')
        
        if transaction.status in ['completed', 'cancelled']:
            raise ValueError(f'Cannot cancel in {transaction.status} status')
        
        transaction.status = 'cancelled'
        transaction.cancelled_at = datetime.utcnow()
        transaction.cancelled_reason = reason
        
        TransactionService._log_transition(
            transaction,
            'cancelled',
            f'Cancelled: {reason}'
        )
        
        db.session.commit()
        return transaction
    
    @staticmethod
    def _log_transition(transaction, new_status, note):
        """Internal: Log status transition"""
        
        if not transaction.status_history:
            transaction.status_history = []
        
        transaction.status_history.append({
            'from': transaction.status,
            'to': new_status,
            'timestamp': datetime.utcnow().isoformat(),
            'note': note
        })
        
        # Update updated_at timestamp
        transaction.updated_at = datetime.utcnow()
        
        db.session.add(transaction)
    
    @staticmethod
    def get_timeline(transaction_id):
        """Get full transaction timeline"""
        
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return None
        
        timeline = {
            'created': {
                'timestamp': transaction.created_at,
                'status': 'pending',
                'description': 'Transaction created'
            }
        }
        
        if transaction.confirmed_at:
            timeline['confirmed'] = {
                'timestamp': transaction.confirmed_at,
                'status': 'confirmed',
                'description': 'Payment confirmed'
            }
        
        if transaction.pickup_scheduled_at:
            timeline['pickup_scheduled'] = {
                'timestamp': transaction.pickup_scheduled_at,
                'status': 'pickup_scheduled',
                'description': f'Pickup scheduled for {transaction.pickup_scheduled_at}'
            }
        
        if transaction.in_transit_at:
            timeline['in_transit'] = {
                'timestamp': transaction.in_transit_at,
                'status': 'in_transit',
                'description': 'Materials picked up'
            }
        
        if transaction.delivered_at:
            timeline['delivered'] = {
                'timestamp': transaction.delivered_at,
                'status': 'delivered',
                'description': 'Materials delivered'
            }
        
        if transaction.completed_at:
            timeline['completed'] = {
                'timestamp': transaction.completed_at,
                'status': 'completed',
                'description': 'Transaction complete'
            }
        
        return timeline
    
    