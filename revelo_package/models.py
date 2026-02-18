from revelo_package import db

class Company(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    name=db.Column(db.String(length=30),nullable=False,unique=True)
    email=db.Column(db.String(length=50),nullable=False,unique=True)
    phone=db.Column(db.String(length=30),nullable=False,unique=True)
    address=db.Column(db.String(length=30),nullable=False)
    password_hash=db.Column(db.String(length=60),nullable=False)
    activity=db.Column(db.String(length=30),nullable=False)
    rc=db.Column(db.String(length=30),nullable=False)
    nif=db.Column(db.String(length=30),nullable=False)
    nis=db.Column(db.String(length=30),nullable=False)
    referal=db.Column(db.String(length=30))
    items=db.relationship('Item', backref='owned_Company',lazy=True)

class Transaction(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    seller=db.relationship('Company',lazy=True)
    buyer=db.relationship('Company', lazy=True)
    shipped=db.Column(db.String(length=30),nullable=False,unique=True)
    received=db.Column(db.String(length=30),nullable=False,unique=True)
    status=db.Column(db.String(length=30),nullable=False,unique=True)
    date_added=db.Column(db.String(length=30),nullable=False,unique=True)


class Item(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    name=db.Column(db.String(length=30),nullable=False)
    description=db.Column(db.String(length=1024))
    location=db.Column(db.String(length=30))
    category=db.Column(db.String(length=30))
    subcategory=db.Column(db.String(length=30))
    sell_type=db.Column(db.String(length=30))
    price=db.Column(db.Integer(),nullable=False) 
    added_date=db.Column(db.String(length=30))
    def __repr__(self):
        return f'Item {self.name}'

class View(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    company=db.relationship('Company',lazy=True)
    item=db.relationship('Item',lazy=True)
