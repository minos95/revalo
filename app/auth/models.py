from datetime import datetime

from wtforms import ValidationError

from app import db,bcrypt,login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
class Company(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    name = db.Column(db.String(length=30),nullable=False,unique=True)
    email = db.Column(db.String(200))
    
    phone = db.Column(db.String(50))
    website = db.Column(db.String(200))
    logo = db.Column(db.String(200))

    rating_avg= db.Column(db.Integer(),default=0)
    total_reviews=db.Column(db.Integer(),default=0)
    
    address = db.Column(db.String(length=30),nullable=False)
    country = db.Column(db.String(length=30),nullable=False)
    city = db.Column(db.String(length=30),nullable=False)
    company_type = db.Column(db.String(length=30),nullable=False) #generator, recycler, trader
    activity = db.Column(db.String(length=30),nullable=False)
    rc = db.Column(db.String(length=30))
    nif = db.Column(db.String(length=30))
    nis = db.Column(db.String(length=30))
    referal = db.Column(db.String(length=30))
    verified=db.Column(db.String(),default="pending")
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    
    items = db.relationship('Item', back_populates='owned_company',lazy=True)
    users = db.relationship('User', back_populates='owned_company',lazy=True)
    buy_transactions=db.relationship('Transaction', back_populates='buyer_company',foreign_keys="Transaction.buyer_company_id",lazy=True)
    sell_transactions=db.relationship('Transaction', back_populates='seller_company',foreign_keys="Transaction.seller_company_id",lazy=True)
    offers = db.relationship("Offer",foreign_keys="Offer.sender_company_id",back_populates="sender_company",lazy=True)
    reviews = db.relationship('Review', back_populates='company')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please log in.')

    def validate_company_email(self, company_email):
        company = Company.query.filter_by(email=company_email.data).first()
        if company:
            raise ValidationError('A company with this email already exists.')
        
class User(db.Model,UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer(),primary_key=True)
    company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    full_name = db.Column(db.String(length=30),nullable=False)
    phone = db.Column(db.String(length=30),nullable=False)
    email = db.Column(db.String(length=50),nullable=False,index=True)
    email_verified=db.Column(db.Boolean(),default=False)
    password_hash=db.Column(db.String(length=50),nullable=False)
    role = db.Column(db.String(length=30),nullable=False)  # owner, manager, employee
    authorized=db.Column(db.Boolean(),default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())


    owned_company = db.relationship("Company", back_populates="users")
    items = db.relationship('Item', back_populates='owned_user',lazy=True)
    notifications = db.relationship('Notification', back_populates='user')

    transactions_as_seller_manager = db.relationship('Transaction',foreign_keys='Transaction.seller_manager_id', back_populates='seller_manager',lazy=True)
    transactions_as_buyer_manager = db.relationship('Transaction',foreign_keys='Transaction.buyer_manager_id',  back_populates='buyer_manager',lazy=True)
    reviews_written = db.relationship('Review', back_populates='reviewer',foreign_keys='Review.reviewer_id')
    @property
    def password(self):
        return self.password
    
    @password.setter
    def password(self,plain_text_password):
        self.password_hash=bcrypt.generate_password_hash(plain_text_password).decode('utf-8')
    def check_password_correction(self,attempted_password):
        return bcrypt.check_password_hash(self.password_hash,attempted_password)
    

class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50))  # 'offer_received', 'offer_accepted', 'listing_sold', etc.
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    related_id = db.Column(db.Integer)  # ID of related offer/listing/transaction
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    
    # Relationships
    user = db.relationship('User', back_populates='notifications')
    
    def __repr__(self):
        return f'<Notification {self.type} for user {self.user_id}>'



class Review(db.Model):
    __tablename__ = 'review'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Company being reviewed
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False, index=True)
    
    # User who wrote the review
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Associated transaction
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), unique=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    
    # Review content
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    
    # Detailed ratings
    communication_rating = db.Column(db.Integer)  # 1-5
    quality_rating = db.Column(db.Integer)  # 1-5
    delivery_rating = db.Column(db.Integer)  # 1-5
    value_rating = db.Column(db.Integer)  # 1-5
    
    # Comments
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    pros = db.Column(db.Text)
    cons = db.Column(db.Text)
    
    # Response from company
    response_text = db.Column(db.Text)
    responded_at = db.Column(db.DateTime)
    responded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Verification
    verified_purchase = db.Column(db.Boolean, default=True)
    
    # Status
    is_approved = db.Column(db.Boolean, default=True)  # For moderation
    is_public = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
     # Relationships
    company = db.relationship('Company', back_populates='reviews')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], back_populates='reviews_written')
    transaction = db.relationship('Transaction', back_populates='review')
    item = db.relationship('Item', back_populates='reviews')
    responder = db.relationship('User', foreign_keys=[responded_by])
    
    def respond(self, response_text, user_id):
        """Add company response to review"""
        self.response_text = response_text
        self.responded_at = datetime.utcnow()
        self.responded_by = user_id
        db.session.commit()
    
    def __repr__(self):
        return f'<Review {self.rating}⭐ for {self.company.name}>'