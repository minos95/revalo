from datetime import datetime

from flask_login import current_user

from app import db

class Transaction(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
     # References
    offer_id = db.Column(db.Integer(),db.ForeignKey('offer.id'))
    item_id = db.Column(db.Integer(),db.ForeignKey('item.id'))
    # Companies involved
    buyer_company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    seller_company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    # Point of contact users
    seller_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    buyer_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))

     # Transaction details
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Numeric(10, 2))
    unit = db.Column(db.String(20), default='kg')
    # Payment
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, refunded, failed
    dilivery_status = db.Column(db.String(length=30),nullable=False,default="pending")

     # Invoice
    invoice_number = db.Column(db.String(100), unique=True)
    invoice_url = db.Column(db.String(255))

     # Logistics
    pickup_scheduled_at = db.Column(db.DateTime)
    pickup_completed_at = db.Column(db.DateTime)
    pickup_notes = db.Column(db.Text)
    
    delivery_scheduled_at = db.Column(db.DateTime)
    delivery_completed_at = db.Column(db.DateTime)
    delivery_notes = db.Column(db.Text)

    # Status tracking
    status = db.Column(db.String(20), default='pending', index=True)  # payment_pending,pending, confirmed, in_transit, completed, cancelled, dispute

    total_amount=db.Column(db.Integer(),nullable=False)
    commission_rate=db.Column(db.Integer(),nullable=False,default='0.07')
    commission_amount=db.Column(db.Integer(),nullable=False)
    seller_net_amount=db.Column(db.Integer(),nullable=False)

     # Waste tracking (important for compliance)
    waste_manifest_number = db.Column(db.String(100))
    waste_manifest_url = db.Column(db.String(255))
    weight_certificate_url = db.Column(db.String(255))
    coa_url = db.Column(db.String(255))  # Certificate of Analysis

        # Timestamps
    confirmed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    cancelled_reason = db.Column(db.Text)

      # Dispute tracking
    is_disputed = db.Column(db.Boolean, default=False)
    dispute_reason = db.Column(db.Text)
    dispute_raised_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    dispute_raised_at = db.Column(db.DateTime)
    dispute_resolved_at = db.Column(db.DateTime)

        # Delivery confirmation (buyer side)
    delivery_confirmed = db.Column(db.Boolean, default=False)
    delivery_confirmed_at = db.Column(db.DateTime)
    delivery_confirmed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Quality acceptance (buyer side)
    quality_accepted = db.Column(db.Boolean, default=False)
    quality_accepted_at = db.Column(db.DateTime)
    quality_notes = db.Column(db.Text)
    rejection_reason = db.Column(db.Text)
    
    # Payment confirmation (seller side)
    payment_confirmed = db.Column(db.Boolean, default=False)
    payment_confirmed_at = db.Column(db.DateTime)
    payment_confirmed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=db.func.now(), onupdate=db.func.now())
  
   
   #references
    
    review = db.relationship("Review", back_populates="owned_review",lazy=True)
    listing = db.relationship("Item", back_populates="transactions",lazy=True)
    buyer_company = db.relationship('Company', back_populates='buy_transactions',foreign_keys=[buyer_company_id],lazy=True)
    seller_company = db.relationship('Company', back_populates='sell_transactions',foreign_keys=[seller_company_id],lazy=True)
    seller_manager = db.relationship('User', foreign_keys=[seller_manager_id],
                                    back_populates='transactions_as_seller_manager')
    buyer_manager = db.relationship('User', foreign_keys=[buyer_manager_id],
                                    back_populates='transactions_as_buyer_manager')
    offer = db.relationship("Offer", back_populates="transaction")

    review = db.relationship('Review', back_populates='transaction')
    
    #conversations= db.relationship('Conversation', backref='transaction')

    def mark_in_transit(self):
        if self.status=="pending" and self.seller_company_id==current_user.company_id:
          print("+++++++++++++++++++++++++++")
          self.status = 'in_transit'
          db.session.commit()
        else :
            raise ValueError('Cannot confirm delivery at this stage')
          
    

    def can_buyer_confirm_delivery(self):
        """Check if buyer can confirm delivery"""
        return (
            self.status == 'in_transit' and
            not self.delivery_confirmed and
            not self.is_disputed
        )
    
    def buyer_confirm_delivery(self, user_id, notes=None):
        """Buyer confirms receipt of materials"""
        if not self.can_buyer_confirm_delivery():
            raise ValueError('Cannot confirm delivery at this stage')
        
        self.delivery_confirmed = True
        self.delivery_confirmed_at = datetime.utcnow()
        self.delivery_confirmed_by = user_id
        
        if notes:
            self.quality_notes = notes
        
        # Move to quality review stage
        self.status = 'quality_review'
        db.session.commit()
    
    def buyer_accept_quality(self, user_id, weight_certificate=None):
        """Buyer accepts material quality"""
        if self.status != 'quality_review':
            raise ValueError('Cannot accept quality at this stage')
        
        self.quality_accepted = True
        self.quality_accepted_at = datetime.utcnow()
        
        if weight_certificate:
            self.weight_certificate_url = weight_certificate
        
        # Move to payment release stage
        self.status = 'payment_pending'
        db.session.commit()
    
    def buyer_reject_quality(self, user_id, reason):
        """Buyer rejects material quality - opens dispute"""
        if self.status != 'quality_review':
            raise ValueError('Cannot reject quality at this stage')
        
        self.is_disputed = True
        self.dispute_reason = reason
        self.dispute_raised_by = user_id
        self.dispute_raised_at = datetime.utcnow()
        self.status = 'disputed'
        db.session.commit()
    
    def seller_confirm_payment(self, user_id):
        """Seller confirms payment received"""
        if self.status != 'payment_pending':
            raise ValueError('Cannot confirm payment at this stage')
        
        self.payment_confirmed = True
        self.payment_confirmed_at = datetime.utcnow()
        self.payment_confirmed_by = user_id
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        db.session.commit()

