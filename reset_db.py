from app import db,app,bcrypt
from app.auth.models import Company,User


with app.app_context():
    db.drop_all()
    db.create_all()

company_admin=Company(name='Admin',
                    address='Oran',
                    country='Algerie',
                    city='Oran', 
                    company_type="Metal",
                    activity="Metal")
user_admin=User(company_id=1,
                full_name='Amine Amine',
                phone='0666666666',
                email="rh@gmail.com",
                email_verified=True,
                password_hash=bcrypt.generate_password_hash("azerty123").decode('utf-8'),
                role="admin",
                authorized=True)

with app.app_context():
    db.session.add(company_admin)
    db.session.add(user_admin)
    db.session.commit()
print('db has been reseted')