
from app import app,db
from app.models import User, Company, Category, Item, Offer, Transaction, Review,Image,View,Quality_attribute_options,Quality_attributes,Item_quality_values
from flask_migrate import Migrate


migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Company': Company,
        'Category': Category,
        'Item': Item,
        'Offer': Offer,
        'Transaction': Transaction,
        'Review': Review,
        'Image':Image,
        'View':View,
        'Quality_attribute_options':Quality_attribute_options,
        'Quality_attributes':Quality_attributes,
        'Item_quality_values':Item_quality_values
        
    }
if __name__=='__main__':
    app.run(debug=True)