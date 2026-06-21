from datetime import datetime, timedelta

from flask import current_app

from app import db


class Item(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    company_id= db.Column(db.Integer(),db.ForeignKey('company.id'))
    category_id= db.Column(db.Integer(),db.ForeignKey('category.id'))
    user_id=db.Column(db.Integer(),db.ForeignKey('user.id'))
    name=db.Column(db.String(length=30),nullable=False)
    description=db.Column(db.String(length=1024))
    unit= db.Column(db.String(length=30),nullable=False)

    #quantity
    quantity= db.Column(db.Numeric(10,2),nullable=False) 
    available_quantity=db.Column(db.Numeric(10,2),default=0)  # Will be overridden by __init__
    sold_quantity = db.Column(db.Numeric(10, 2), default=0)     # From accepted offers

    #Price
    price=db.Column(db.Numeric(10,2)) 
    price_negotiable = db.Column(db.Boolean, default=True)


    minimum_order = db.Column(db.Numeric(10, 2), default=0)
    views=db.Column(db.Integer(),default=0)
    #pickup field
    pickup_address=db.Column(db.String(length=30))
    pickup_city=db.Column(db.String(length=30))
    pickup_country=db.Column(db.String(length=30))

    sell_type=db.Column(db.String(length=30))
    
    status=db.Column(db.String(length=30),default="draft") #active/closed/sold/published/pending
    expires_at= db.Column(db.DateTime())
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    # Subscription tracking
    is_featured = db.Column(db.Boolean, default=False)  # Featured listing (paid extra)
    featured_expires_at = db.Column(db.DateTime)  # When featured expires
    boost_score = db.Column(db.Integer, default=0)  # For search ranking
    
    


    images=db.relationship('Image',backref='owned_item',lazy=True)
    owned_user = db.relationship("User", back_populates="items")
    owned_company = db.relationship("Company", back_populates="items")
    owned_category=db.relationship("Category",back_populates="items")
    offers = db.relationship('Offer', back_populates='item',lazy=True)
    transactions = db.relationship('Transaction', back_populates='listing',lazy=True)
    images = db.relationship('Image', back_populates='owned_image',lazy=True)
    qualities = db.relationship('Item_quality_values', back_populates='owned_item',lazy=True)
    reviews = db.relationship('Review', back_populates='item')
    #conversation
    #conversations= db.relationship('Conversation', backref='item')
    
    
    def __repr__(self):
        return f'Item {self.name}'
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Extract total_quantity if provided
        total = kwargs.get('quantity', 0)
        
        # Set available_quantity to match total_quantity
        if 'available_quantity' not in kwargs:
            kwargs['available_quantity'] = total
        
        if not self.expires_at:
            days = current_app.config.get('LISTING_EXPIRY_DAYS', 30)
            self.expires_at = datetime.utcnow() + timedelta(days=days)
    
    @property
    def is_expired(self):
        return self.expires_at and db.func.now() > self.expires_at
    # Subscription tracking
    def can_be_featured(self):
        """Check if listing can be featured based on subscription"""
        company = self.company
        if company.has_active_subscription():
            featured_count = Item.query.filter_by(
                company_id=company.id,
                is_featured=True
            ).count()
            return featured_count < company.max_featured_listings
        return False
    #available quantity
  
    

class Image(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    item_id= db.Column(db.Integer(),db.ForeignKey('item.id'))
    default=db.Column(db.Boolean(),default=False)
    uri=db.Column(db.String(length=30))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    owned_image = db.relationship('Item', back_populates='images',lazy=True)
    

class View(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    company_id= db.Column(db.Integer(),db.ForeignKey('company.id'))
    item_id=db.Column(db.Integer(),db.ForeignKey('item.id'))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())



class Category(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    name=db.Column(db.String(length=30),nullable=False)
    Description=db.Column(db.String(length=300),nullable=False)
    default_image_url = db.Column(db.String(255))
   
    items=db.relationship("Item", back_populates="owned_category",lazy=True)
    qualities = db.relationship('Quality_attributes', back_populates='owned_quality',lazy=True)
     
    
class Quality_attributes(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    category_id= db.Column(db.Integer(),db.ForeignKey('category.id'))
    name=db.Column(db.String(length=30),nullable=False) #--- cleanliness, Compressed, Rust level, Crushed
    field=db.Column(db.String(length=30),nullable=False) #-----select,boolean,number,text
    unit=db.Column(db.String(length=30))
    is_required=db.Column(db.Boolean())
    owned_quality = db.relationship('Category', back_populates='qualities',lazy=True)
    options=db.relationship('Quality_attribute_options', back_populates='owned_attribute_options',lazy=True)
    qualities= db.relationship('Item_quality_values', back_populates='attribute',lazy=True)

    def __repr__(self):
        return f'{self.name}'
class Quality_attribute_options(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    attribute_id= db.Column(db.Integer(),db.ForeignKey('quality_attributes.id'))
    value=db.Column(db.String(length=30),nullable=False) #----cleanliness: clean ,mixed dirty, rust level: low,medium,high
    owned_attribute_options=db.relationship('Quality_attributes', back_populates='options',lazy=True)
    items=db.relationship('Item_quality_values', back_populates='option',lazy=True)
class Item_quality_values(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    item_id= db.Column(db.Integer(),db.ForeignKey('item.id'))
    attribute_id= db.Column(db.Integer(),db.ForeignKey('quality_attributes.id'))
    option_id=db.Column(db.Integer(),db.ForeignKey('quality_attribute_options.id'))
    value_text=db.Column(db.String(length=30))
    value_number=db.Column(db.Integer())
    owned_item = db.relationship('Item', back_populates='qualities',lazy=True)
    attribute= db.relationship('Quality_attributes', back_populates='qualities',lazy=True)
    option=db.relationship('Quality_attribute_options', back_populates='items',lazy=True)