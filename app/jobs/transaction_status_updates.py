
from datetime import datetime, timedelta

from app.transactions.models import Transaction


def auto_update_transaction_status():
    """Automatically update transaction statuses"""
    
    # Find transactions pending delivery confirmation
    delivered_but_not_completed = Transaction.query.filter(
        Transaction.status == 'delivered',
        Transaction.delivery_completed_at < datetime.utcnow() - timedelta(days=3)
    ).all()
    
    for transaction in delivered_but_not_completed:
        # Auto-complete after 3 days if no dispute
        transaction.status = 'completed'
        transaction.completed_at = datetime.utcnow()
        transaction.payment_status = 'released'
        
        # Update stats
        transaction.seller_company.total_transactions += 1
        transaction.seller_company.total_revenue += transaction.final_price
        transaction.buyer_company.total_transactions += 1
        
        db.session.commit()
        
        # Notify both parties
        notify_auto_completed(transaction)