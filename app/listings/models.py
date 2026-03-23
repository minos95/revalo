from app import db


class Item(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    company_id= db.Column(db.Integer(),db.ForeignKey('company.id'))
    category_id= db.Column(db.Integer(),db.ForeignKey('category.id'))
    user_id=db.Column(db.Integer(),db.ForeignKey('user.id'))
    name=db.Column(db.String(length=30),nullable=False)
    description=db.Column(db.String(length=1024))
    unit= db.Column(db.String(length=30),nullable=False)
    quantity= db.Column(db.Integer(),nullable=False) 
    price_negotiable = db.Column(db.Boolean, default=True)
    minimum_order = db.Column(db.Numeric(10, 2), default=0)
    views=db.Column(db.Integer())
    #pickup field
    pickup_address=db.Column(db.String(length=30))
    pickup_city=db.Column(db.String(length=30))
    pickup_country=db.Column(db.String(length=30))

    sell_type=db.Column(db.String(length=30))
    price=db.Column(db.Integer(),nullable=False) 
    status=db.Column(db.String(length=30),default="pending") #active/closed/sold
    expires_at= db.Column(db.DateTime())
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    images=db.relationship('Image',backref='owned_item',lazy=True)
    offers=db.relationship('Offer',backref='owned_item',lazy=True)
    views=db.relationship('View',backref='owned_item',lazy=True)
    owned_user = db.relationship("User", back_populates="items")
    owned_company = db.relationship("Company", back_populates="items")
    owned_category=db.relationship("Category",back_populates="items")
    offers = db.relationship('Offer', back_populates='owned_offer',lazy=True)
    transactions = db.relationship('Transaction', back_populates='listing',lazy=True)
    images = db.relationship('Image', back_populates='owned_image',lazy=True)
    qualities = db.relationship('Item_quality_values', back_populates='owned_item',lazy=True)
    
    
    def __repr__(self):
        return f'Item {self.name}'
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            if not self.expires_at:
                days = current_app.config.get('LISTING_EXPIRY_DAYS', 30)
                self.expires_at = datetime.utcnow() + timedelta(days=days)
    
    @property
    def is_expired(self):
        return self.expires_at and db.func.now() > self.expires_at

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

class Review(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    transaction_id= db.Column(db.Integer(),db.ForeignKey('transaction.id'))
    reviewer_company_id = db.Column(db.Integer(),nullable=False)
    reviewed_company_id = db.Column(db.Integer(),nullable=False)
    comment = db.Column(db.String(length=300),nullable=False)
    rating = db.Column(db.Integer(),nullable=False) #1-5
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    owned_review = db.relationship("Transaction", back_populates="review",lazy=True)


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