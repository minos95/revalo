from app import db
class Offer(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    item_id = db.Column(db.Integer(),db.ForeignKey('item.id'))
    buyer_company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    seller_company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    sender_company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    buyer_id=db.Column(db.Integer(),db.ForeignKey('user.id'))
    seller_id=db.Column(db.Integer(),db.ForeignKey('user.id'))
    offered_price = db.Column(db.Numeric(10,2),nullable=False)
    quantity_requested = db.Column(db.Numeric(10,2),nullable=False)
    unit = db.Column(db.String(length=300),nullable=False)
    message = db.Column(db.String(length=300))
    status = db.Column(db.String(length=30),default="pending")#pending/countred/accepted/rejected/cancelled/expired
    requires_delivery=db.Column(db.Boolean(),default=False)
    delivery_address=db.Column(db.String(length=100))

    # Negotiation system
    parent_offer_id = db.Column(db.Integer, db.ForeignKey("offer.id"), nullable=True)
    is_counter = db.Column(db.Boolean, default=False)

    expires_at = db.Column(db.DateTime)
    responded_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    accepted_at=db.Column(db.DateTime(timezone=True))
    item = db.relationship("Item", back_populates="offers")
    sender_company = db.relationship("Company",foreign_keys=[sender_company_id],back_populates="offers")
    transaction = db.relationship("Transaction", back_populates="offer",uselist=False)