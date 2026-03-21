from revelo_package import app,db
from revelo_package.models import Category
from revelo_package.models import Quality_attributes
from revelo_package.models import Quality_attribute_options


def seed_categories():

    data = {
        "Plastic": {
            "Type": ["PET", "HDPE", "LDPE", "PP", "PVC"],
            "Form": ["Bottles", "Flakes", "Granules", "Film"],
            "Cleanliness": ["Clean", "Dirty"],
            "Color": ["Transparent", "Blue", "Green", "Mixed"],
            "Packaging": ["Baled", "Loose"]
        },

        "Metal": {
            "Type": ["Aluminum", "Steel", "Copper"],
            "Form": ["Scrap", "Sheets", "Wires"],
            "Condition": ["Clean", "Rusty"],
            "Grade": ["High", "Medium", "Low"]
        },

        "Paper": {
            "Type": ["Cardboard", "Office Paper", "Newspaper"],
            "Quality": ["Clean", "Mixed", "Wet"],
            "Packaging": ["Baled", "Loose"]
        }
    }

    for category_name, attributes in data.items():

        category = Category(name=category_name,Description="")
        db.session.add(category)
        db.session.flush()

        for attr_name, values in attributes.items():

            attribute = Quality_attributes(
                name=attr_name,
                category_id=category.id,
                field="select"
            )
            db.session.add(attribute)
            db.session.flush()

            for val in values:
                value = Quality_attribute_options(
                    value=val,
                    attribute_id=attribute.id
                )
                db.session.add(value)

    db.session.commit()

    print("✅ Categories seeded successfully!")

with app.app_context():
    seed_categories()