from datetime import datetime
from app import db

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic info
    name = db.Column(db.String(50), nullable=False)  # Free, Basic, Pro, Enterprise
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Pricing
    price_monthly = db.Column(db.Numeric(10, 2), default=0)
    price_yearly = db.Column(db.Numeric(10, 2), default=0)
    currency = db.Column(db.String(3), default='DA')
    
    # Stripe IDs
    stripe_price_id_monthly = db.Column(db.String(100))
    stripe_price_id_yearly = db.Column(db.String(100))
    stripe_product_id = db.Column(db.String(100))
    
    # Features & Limits
    max_active_listings = db.Column(db.Integer, default=0)
    max_featured_listings = db.Column(db.Integer, default=0)
    max_team_members = db.Column(db.Integer, default=1)
    max_monthly_transactions = db.Column(db.Integer, default=0)
    commission_rate = db.Column(db.Numeric(5, 2), default=5.0)
    
    # Feature flags
    has_analytics = db.Column(db.Boolean, default=False)
    has_api_access = db.Column(db.Boolean, default=False)
    has_priority_support = db.Column(db.Boolean, default=False)
    has_bulk_upload = db.Column(db.Boolean, default=False)
    has_advanced_filters = db.Column(db.Boolean, default=False)
    has_dedicated_manager = db.Column(db.Boolean, default=False)
    
    # Display order
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    is_popular = db.Column(db.Boolean, default=False)
    
    # Metadata
    features_list = db.Column(db.JSON)  # Array of feature strings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    companies = db.relationship('Company', back_populates='subscription_plan')
    
    def get_price_display(self, interval='monthly'):
        """Get formatted price display"""
        if interval == 'monthly':
            return f"${self.price_monthly}/month"
        return f"${self.price_yearly}/year"
    
    def get_savings_percentage(self):
        """Calculate yearly savings percentage"""
        if self.price_monthly > 0 and self.price_yearly > 0:
            yearly_monthly = self.price_monthly * 12
            savings = ((yearly_monthly - self.price_yearly) / yearly_monthly) * 100
            return round(savings)
        return 0
    
    def get_features_list(self):
        """Get list of features for display"""
        features = []
        
        if self.max_active_listings:
            features.append(f"Up to {self.max_active_listings} active listings")
        if self.max_featured_listings:
            features.append(f"{self.max_featured_listings} featured listings")
        if self.max_team_members > 1:
            features.append(f"Up to {self.max_team_members} team members")
        if self.commission_rate < 8:
            features.append(f"{self.commission_rate}% commission rate")
        if self.has_analytics:
            features.append("Advanced analytics dashboard")
        if self.has_api_access:
            features.append("API access")
        if self.has_priority_support:
            features.append("Priority support")
        if self.has_bulk_upload:
            features.append("Bulk listing upload")
        if self.has_advanced_filters:
            features.append("Advanced search filters")
        if self.has_dedicated_manager:
            features.append("Dedicated account manager")
        
        return features
    
    def __repr__(self):
        return f'<SubscriptionPlan {self.name} - ${self.price_monthly}>'
    

class SubscriptionPayment(db.Model):
    __tablename__ = 'subscription_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    
    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='DA')
    interval = db.Column(db.String(10))  # monthly, yearly
    
    # Dates
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Invoice
    invoice_number = db.Column(db.String(100), unique=True)
    invoice_url = db.Column(db.String(500))
    
    # Payment method
    payment_method = db.Column(db.String(50))  # stripe, paypal, manual
    payment_method_details = db.Column(db.JSON)
    
    # Stripe/ Gateway IDs
    stripe_payment_intent_id = db.Column(db.String(100))
    stripe_invoice_id = db.Column(db.String(100))
    receipt_url = db.Column(db.String(500))
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, succeeded, failed, refunded
    failure_reason = db.Column(db.Text)
    
    # Metadata
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', back_populates='subscription_payments')
    subscription_plan = db.relationship('SubscriptionPlan')
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        import random
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        random_num = random.randint(1000, 9999)
        self.invoice_number = f"SUB-{timestamp}-{self.company_id}-{random_num}"
        return self.invoice_number
    
    def __repr__(self):
        return f'<SubscriptionPayment {self.invoice_number} - ${self.amount}>'