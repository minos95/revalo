from app import app,db
from app.listings.models import Category,Quality_attributes,Quality_attribute_options



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
            "Type": ["Steel","Iron","Aluminum","Copper","Brass","Mixed metals"],
            "Form": ["Sheets","Pipes","Wires","Shavings","Mixed scrap"],
            "Condition": ["Clean","Oily","Painted","Rusty"],
            "Size":["Small pieces","Medium","Large pieces"]
            },

        "Paper & Cardboard": {
            "Type": ["Cardboard", "Office Paper", "Newspaper","Mixed paper"],
            "Cleanliness": ["Clean", "Mixed", "Contaminated"],
            "Condition":["Dry","Slightly wet","Wet"],
            "Packaging": ["Baled", "Loose"],
           
        },
        "Construction":{
            "Type":
            ["Brick","Concrete","Tiles","Asphalt","Mixed rubble"],
            "Condition":
            ["Whole pieces","Crushed","Powder"],
            "Contamination":
            ["Clean","Mixed with soil","Mixed with other materials"],
            "Reuse Condition":["Ready for reuse","Requires processing"],
        },

       " E-Waste (Electronic Waste)":{
           "Type":
            ["Computers","Servers","Mobile phones","TVs","Cables",
            "Circuit boards"],
            "Condition":["Working","Non-working","For parts"],
            "Completeness":["Complete device","Missing parts","Components only"]
       },
       "Wood & Pallets":{
           "Type":["Pallets","Solid wood","Plywood","Mixed wood"],
           "Condition":["Reusable","Damaged","Scrap"],
            "Treatment":["Untreated","Treated / painted"]
            },
       
        "Textile":{
            "Type":["Cotton","Polyester","Mixed fabric",],
            "Condition":["Clean","Slightly used","Damaged"],
            "Form":["Clothing","Fabric rolls","Scrap pieces"]
            },
        "Batteries":{
            "Form Factor": ["Automotive", "Industrial", "Consumer", "Button", "Pack",],
            "Chemistry":	["Lead-Acid", "Li-Ion", "Alkaline", "Ni-Cd", "Ni-MH"]
        },
        "Organic":{
            "Type":	["Food", "Yard", "Agricultural", "Wood", "Biosolids"]
        },
         "Glass":{
            "Type":["Bottles","Flat glass","Mixed glass"],
            "Color":["Clear","Green","Brown","Mixed"],
            "Condition":["Whole","Broken"],
        },
        "Medical":{

        }


    }

    for category_name, attributes in data.items():

        category = Category(name=category_name,default_image_url=f"uploads/categories/{category_name}.jpg",description="")
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