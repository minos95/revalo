from app import db






class Offer(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    item_id = db.Column(db.Integer(),db.ForeignKey('item.id'))
    buyer_company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    seller_company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    sender_company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    buyer_id=db.Column(db.Integer(),db.ForeignKey('user.id'))
    seller_id=db.Column(db.Integer(),db.ForeignKey('user.id'))
    offered_price = db.Column(db.Integer(),nullable=False)
    quantity_requested = db.Column(db.Integer(),nullable=False)
    unit = db.Column(db.String(length=300),nullable=False)
    message = db.Column(db.String(length=300))
    status = db.Column(db.String(length=30),default="pending")#pending/countred/accepted/rejected/cancelled/expired
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    accepted_at=db.Column(db.DateTime(timezone=True))
    owned_offer = db.relationship("Item", back_populates="offers")
    sender_company = db.relationship("Company",foreign_keys=[sender_company_id],back_populates="offers")

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
    status = db.Column(db.String(20), default='pending', index=True)  # pending, confirmed, in_transit, completed, cancelled, dispute

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


