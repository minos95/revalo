from collections import namedtuple
from datetime import datetime, timedelta

from wtforms import ValidationError

from app import db,bcrypt,login_manager
from flask_login import UserMixin,current_user
from sqlalchemy import func
from dataclasses import dataclass
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
    total_transactions=db.Column(db.Integer(),default=0)
    total_revenue=db.Column(db.Integer(),default=0)

    address = db.Column(db.String(length=30),nullable=False)
    country = db.Column(db.String(length=30),nullable=False)
    city = db.Column(db.String(length=30),nullable=False)
    Postal_code = db.Column(db.String(length=30))
    company_type = db.Column(db.String(length=30),nullable=False) #generator, recycler, trader
    activity = db.Column(db.String(length=30),nullable=False)
    rc = db.Column(db.String(length=30))
    nif = db.Column(db.String(length=30))
    nis = db.Column(db.String(length=30))
    referal = db.Column(db.String(length=30))
    verified=db.Column(db.Boolean(),default=False)
    verified_by= db.Column(db.Integer())
    verified_at=db.Column(db.DateTime(timezone=True))
      # Grace period tracking
    subscription_grace_period_ends = db.Column(db.DateTime)
    subscription_grace_period_used = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

     # ========== SUBSCRIPTION FIELDS ==========
    
    # Current subscription
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=True)
    # temporary for pending payment 
    subscription_plan_id_temporary = db.Column(db.Integer)

    subscription_status = db.Column(db.String(20), default='free')  # free, active, past_due, cancelled, expired
    subscription_started_at = db.Column(db.DateTime)
    subscription_ends_at = db.Column(db.DateTime)
    subscription_cancelled_at = db.Column(db.DateTime)
    
    # Limits based on subscription
    max_active_listings = db.Column(db.Integer, default=3)      # Free tier: 3 listings
    max_featured_listings = db.Column(db.Integer, default=0)
    max_team_members = db.Column(db.Integer, default=1)
    max_monthly_transactions = db.Column(db.Integer, default=10)
    commission_rate = db.Column(db.Numeric(5, 2), default=0.0)  # 8% for free tier
    
    # Auto-renewal
    auto_renew = db.Column(db.Boolean, default=True)

   
    
    # Stripe/ Payment fields
    stripe_customer_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100))
    default_payment_method_id = db.Column(db.String(100))
    
    # Usage tracking (for billing)
    current_listings_created = db.Column(db.Integer, default=0)
    current_month_listings_created = db.Column(db.Integer, default=0)
    current_month_transactions = db.Column(db.Integer, default=0)
    last_reset_date = db.Column(db.DateTime, default=datetime.now)
    
    # Subscription history tracking
    last_invoice_url = db.Column(db.String(500))
    last_payment_date = db.Column(db.DateTime)
    last_payment_amount = db.Column(db.Numeric(10, 2))
    
    # Relationships
    subscription_plan = db.relationship('SubscriptionPlan', back_populates='companies')
    subscription_payments = db.relationship('SubscriptionPayment', back_populates='company', lazy='dynamic')

    
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
        
     # ========== SUBSCRIPTION HELPER METHODS ==========
    
    def has_active_subscription(self):
        """Check if company has active subscription"""
        return (self.subscription_status == 'active' and 
                self.subscription_ends_at and 
                self.subscription_ends_at > datetime.now())
    
    def can_create_listing(self):
        """Check if company can create new listing based on limits"""

        from app.listings.models import Item as Listing
        
        
        active_listings_count =Listing.query.filter_by(
            company_id=self.id,
            status='active'
        ).count()
        
        return active_listings_count < self.max_active_listings
  
    
    def can_add_team_member(self):
        """Check if company can add more team members"""
        current_members = User.query.filter_by(company_id=self.id).count()
        return current_members < self.max_team_members
    
    def get_remaining_listings(self):
        """Get remaining listing quota"""
        from app.listings.models import Item as Listing
        active_listings = Listing.query.filter_by(
            company_id=self.id,
            status='active'
        ).count()
        return max(0, self.max_active_listings - active_listings)
    
    def get_commission_rate_for_transaction(self):
        """Get commission rate for this company"""
        if self.has_active_subscription():
            return self.commission_rate
        return 8.0  # Free tier default
    
    def reset_monthly_usage(self):
        """Reset monthly counters (call via cron job)"""
        self.current_month_listings_created = 0
        self.current_month_transactions = 0
        self.last_reset_date = datetime.now()
        db.session.commit()
    
    def increment_listings_created(self):
        """Increment monthly listing count"""
        self.current_month_listings_created += 1
        db.session.commit()
    
    def increment_transactions(self):
        """Increment monthly transaction count"""
        self.current_month_transactions += 1
        
        # Check if over limit
        if self.current_month_transactions > self.max_monthly_transactions:
            # Could trigger notification or automatic upgrade
            pass
        
        db.session.commit()
    
    def cancel_subscription(self):
        """Cancel subscription at end of period"""
        self.subscription_status = 'cancelled'
        self.subscription_cancelled_at = datetime.now()
        self.auto_renew = False
        db.session.commit()
    
    @property
    def is_in_grace_period(self):
        """Check if company is in grace period"""
        if not self.subscription_grace_period_ends:
            return False
        return datetime.now() < self.subscription_grace_period_ends
    
    @property
    def days_left_in_grace(self):
        """Days left in grace period"""
        if not self.subscription_grace_period_ends:
            return 0
        if datetime.now() > self.subscription_grace_period_ends:
            return 0
        return (self.subscription_grace_period_ends - datetime.now()).days
    
    def start_grace_period(self, days=14):
        """Start grace period after payment failure"""
        self.subscription_grace_period_ends = datetime.now() + timedelta(days=days)
        self.subscription_grace_period_used = True
        self.subscription_status = 'grace_period'
        db.session.commit()
    
    def downgrade_to_free(self):
        """Downgrade to free plan"""
        free_plan = db.SubscriptionPlan.query.filter_by(slug='free').first()
        
        if free_plan:
            self.subscription_plan_id = free_plan.id
            self.max_active_listings = free_plan.max_active_listings
            self.max_featured_listings = free_plan.max_featured_listings
            self.max_team_members = free_plan.max_team_members
            self.max_monthly_transactions = free_plan.max_monthly_transactions
            self.commission_rate = free_plan.commission_rate
        
        self.subscription_status = 'expired'
        self.subscription_grace_period_ends = None
        db.session.commit()
        
        # Archive excess listings
        self.archive_excess_listings()
    
    def archive_excess_listings(self):
        """Archive listings exceeding free plan limit"""
        active_listings = db.Item.query.filter_by(
            company_id=self.id,
            status='active'
        ).count()
        
        if active_listings > self.max_active_listings:
            # Archive oldest listings first
            excess = active_listings - self.max_active_listings
            listings_to_archive = db.Item.query.filter_by(
                company_id=self.id,
                status='active'
            ).order_by(db.Item.created_at).limit(excess).all()
            
            for listing in listings_to_archive:
                listing.status = 'archived'
                listing.archived_reason = 'subscription_expired'
        
        db.session.commit()

    
    def __repr__(self):
        return f'<Company {self.name} - Plan: {self.subscription_plan.name if self.subscription_plan else "Free"}>'
    
   
class User(db.Model,UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer(),primary_key=True)
    company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    full_name = db.Column(db.String(length=30),nullable=False)
    avatar_url= db.Column(db.String(length=30))
    phone = db.Column(db.String(length=30))
    email = db.Column(db.String(length=50),nullable=False,index=True)
    email_verified=db.Column(db.Boolean(),default=False)
    password_hash=db.Column(db.String(length=50),nullable=False)
    role = db.Column(db.String(length=30),nullable=False)  # owner, manager, employee
    job_title =db.Column(db.String(length=30))
    department =db.Column(db.String(length=30))
    notification_preferences =db.Column(db.String(length=30))
     # Password reset fields
    reset_password_token = db.Column(db.String(100), unique=True, index=True)
    reset_password_expires = db.Column(db.DateTime)
    
    # Email verification fields
    email_verification_token = db.Column(db.String(100), unique=True)
    email_verified = db.Column(db.Boolean, default=False)


    authorized=db.Column(db.Boolean(),default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())


    owned_company = db.relationship("Company", back_populates="users")
    items = db.relationship('Item', back_populates='owned_user',lazy=True)
    notifications = db.relationship('Notification', back_populates='user')

    transactions_as_seller_manager = db.relationship('Transaction',foreign_keys='Transaction.seller_manager_id', back_populates='seller_manager',lazy=True)
    transactions_as_buyer_manager = db.relationship('Transaction',foreign_keys='Transaction.buyer_manager_id',  back_populates='buyer_manager',lazy=True)
    reviews_written = db.relationship('Review', back_populates='reviewer',foreign_keys='Review.reviewer_id')
    
    #Conversation
    #seller_conversations= db.relationship('Conversation', foreign_keys='Conversation.seller_id', backref='seller')
    #buyer_conversations= db.relationship('Conversation', foreign_keys='Conversation.buyer_id', backref='buyer')
   
    @property
    def unread_notification_count(self):
        """Get unread notification count for this user"""
        from app.auth.models import Notification
        from datetime import datetime
        Notif = namedtuple('Notif', ['related_type', 'related_type_count'])
        result=Notification.query.with_entities(
                Notification.related_type, 
                func.count(Notification.id).label("related_type_count")
                ).group_by(Notification.related_type).filter_by(is_read=False,user_id=current_user.id).all()
        result_object={}
        for res in result:
            result_object[res.related_type]=res.related_type_count
        return result_object
    
    @property
    def password(self):
        return self.password
    
    @password.setter
    def password(self,plain_text_password):
        self.password_hash=bcrypt.generate_password_hash(plain_text_password).decode('utf-8')
    def check_password_correction(self,attempted_password):
        return bcrypt.check_password_hash(self.password_hash,attempted_password)
    

    # reset password

    def set_password(self,password):
        self.password=password
        db.session.commit()
    def generate_reset_token(self):
        """Generate a password reset token"""
        import secrets
        token = secrets.token_urlsafe(32)
        self.reset_password_token = token
        self.reset_password_expires = datetime.now() + timedelta(hours=24)
        db.session.commit()
        return token
    
    def verify_reset_token(self, token):
        """Verify reset token is valid"""
        return (self.reset_password_token == token and 
                self.reset_password_expires and 
                self.reset_password_expires > datetime.now())
    
    def clear_reset_token(self):
        """Clear reset token after use"""
        self.reset_password_token = None
        self.reset_password_expires = None
        db.session.commit()
    

class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # Notification content
    type = db.Column(db.String(50), nullable=False)  # offer, transaction, message, system, alert
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Related entity
    related_type = db.Column(db.String(50))  # offer, listing, transaction, conversation
    related_id = db.Column(db.Integer)
    
    # Priority levels
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    # Delivery status
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime)
    sms_sent = db.Column(db.Boolean, default=False)
    sms_sent_at = db.Column(db.DateTime)
    
    
    
    # Expiry
    expires_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    user = db.relationship('User', back_populates='notifications')
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.now()
            db.session.commit()
    
    def is_expired(self):
        """Check if notification has expired"""
        return self.expires_at and datetime.now() > self.expires_at
    
    def get_icon(self):
        """Get icon based on notification type"""
        icons = {
            'offer_received': 'fas fa-handshake',
            'offer_accepted': 'fas fa-check-circle',
            'offer_rejected': 'fas fa-times-circle',
            'offer_countered': 'fas fa-exchange-alt',
            'transaction_created': 'fas fa-shopping-cart',
            'payment_received': 'fas fa-dollar-sign',
            'payment_confirmed': 'fas fa-check-double',
            'message': 'fas fa-envelope',
            'listing_expired': 'fas fa-clock',
            'listing_approved': 'fas fa-check',
            'listing_rejected': 'fas fa-ban',
            'system': 'fas fa-bell',
            'alert': 'fas fa-exclamation-triangle'
        }
        return icons.get(self.type, 'fas fa-bell')
    
    def get_color(self):
        """Get color based on priority"""
        colors = {
            'low': 'gray',
            'normal': 'blue',
            'high': 'orange',
            'urgent': 'red'
        }
        return colors.get(self.priority, 'blue')
    
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
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
     # Relationships
    company = db.relationship('Company', back_populates='reviews')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], back_populates='reviews_written')
    transaction = db.relationship('Transaction', back_populates='review')
    item = db.relationship('Item', back_populates='reviews')
    responder = db.relationship('User', foreign_keys=[responded_by])
    
    def respond(self, response_text, user_id):
        """Add company response to review"""
        self.response_text = response_text
        self.responded_at = datetime.now()
        self.responded_by = user_id
        db.session.commit()
    
    def __repr__(self):
        return f'<Review {self.rating}⭐ for {self.company.name}>'
    

