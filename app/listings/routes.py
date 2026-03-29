from datetime import datetime
import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import  desc

from app import db,app
from app.listings import bp
from app.auth.models import Review
from app.listings.forms import FilterMarketForm, postItemForm
from app.listings.models import Category, Image, Item, Item_quality_values, Quality_attributes
from app.offers.models import Offer
from app.transactions.models import Transaction
from werkzeug.utils import secure_filename

from app.offers.forms import makeOfferForm




"""-----------------------------Market Routes ----------------------"""

@bp.route("/market/category")
def market_category():
    categories=Category.query.all()
    return render_template('market_category.html',categories=categories)

@bp.route("/market/category/<int:category_id>/show",methods=['POST','GET'])
#@login_required
def market(category_id):
    
    page = request.args.get("page_num", 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    form=FilterMarketForm()
    filters=[]
    attributes=Quality_attributes.query.filter_by(category_id=category_id).all()
    print (attributes)
    if category_id!='all':
        filters.append(Item.category_id==category_id)
    if request.args.get("name"):
        filters.append(Item.name.ilike(f"%{request.args.get("name")}%"))
    if request.args.get("category"):
        filters.append(Item.category_id==request.args.get("category"))
    if request.args.get("quantity"):
        filters.append(request.args.get("quantity")<=Item.quantity)
    if request.args.get("location"):
        filters.append(Item.location==request.args.get("location"))
    if   list(set(request.args) & set(attributes)):
         print("-------------++++++++++++++++++++++")
         print(request.args)

    if filters:   
            listings=Item.query.filter(*filters).paginate(page=page,per_page=per_page,error_out=False)
    else:
            listings=Item.query.paginate(page=page,per_page=per_page,error_out=False)

    
 
    return render_template('market.html',listings=listings,form=form,category_id=category_id,attributes=attributes)



"""-------------------------------Listings route---------------------------"""




@bp.route("/")
def listings():
        status = request.args.get('status', 'active')
    
        query = Item.query.filter_by(company_id=current_user.company_id)
        
        if status == 'active':
            query = query.filter_by(status='active').filter(Item.expires_at > datetime.utcnow())
        elif status == 'pending':
            query = query.filter_by(status='pending')
        elif status == 'sold':
            query = query.filter_by(status='sold')
        else:
            query = query.filter(Item.expires_at <= datetime.utcnow())
        
        listings = query.order_by(Item.created_at.desc()).all()
        listings_count=query.count()

        counts = {
        'active': Item.query.filter_by(company_id=current_user.company_id, status='active').count(),
        'pending': Item.query.filter_by(company_id=current_user.company_id, status='pending').count(),
        'sold': Item.query.filter_by(company_id=current_user.company_id, status='sold').count(),
        'expired': Item.query.filter(
            Item.company_id == current_user.company_id,
            Item.expires_at <= datetime.utcnow()
                                    ).count()
                }
       
        return render_template('listings_index.html',listings=listings,status=status,**counts,listings_count=listings_count)


@bp.route("/category")
def listing_select_category():
   
    categories=Category.query.all()
    
    return render_template('listing_select_category.html',categories=categories)
    
@bp.route('/category/<int:category_id>/post',methods=['GET','POST'])
def post(category_id):
    category=Category.query.filter_by(id=category_id).all()
    quality_attributes=Quality_attributes.query.filter_by(category_id=category_id).all()
    form=postItemForm()

   
    if form.validate_on_submit():
        quality_item_to_create=[]
        image_to_create=[]
        item_to_create=Item(name=form.name.data,
                            company_id=current_user.company_id,
                            user_id=current_user.id,
                            description=form.description.data,
                            category_id=category_id,
                            unit=form.unit.data,
                            quantity=form.quantity.data,
                            pickup_address=form.pickup_address.data,
                            pickup_city=form.pickup_city.data,
                            pickup_country=form.pickup_country.data,
                            price_negotiable=form.price_negotiable.data,
                            price=form.price.data,
                            )
        db.session.add(item_to_create)
        db.session.flush()
        for attribute in quality_attributes:
            attr=attribute.name
            quality_item_to_create.append(Item_quality_values(item_id=item_to_create.id,                                                        
                                                       attribute_id=attribute.id,
                                                        option_id=request.form[f"attr_{attribute.id}" ]
                                                        ))
        for image in form.images.data:
            if image:
                filename = secure_filename(image.filename)
                file_path=app.config['UPLOAD_FOLDER']+'listings/'
                file_path = os.path.join(file_path, filename)
                print(file_path)
                image.save(file_path)
                image_to_create.append(Image(item_id=item_to_create.id, 
                                             uri='uploads/listings/'+filename))
        db.session.add_all(image_to_create)
        db.session.add_all(quality_item_to_create)
        db.session.commit()
        
        # Store in session for review
        session['pending_listing_id'] = item_to_create.id
        
        flash('Listing created! Please review before publishing.', 'success')
        return redirect(url_for('listings.listing_review', listing_id=item_to_create.id))
    if form.errors!={}:
        for err_msg in form.errors.values():
                flash(f'error {err_msg}',category='danger')

        # Pre-fill location from company profile
    if request.method == 'GET':
        form.pickup_address.data = current_user.owned_company.address
        form.pickup_city.data = current_user.owned_company.city
        form.pickup_country.data = current_user.owned_company.country
       
    return render_template('listing_post.html',form=form,quality_attributes=quality_attributes,category=category)

@bp.route('/review/<int:listing_id>')
@login_required
def review(listing_id):
    """Step 3: Review listing before publishing"""
    listing = Item.query.get_or_404(listing_id)
    
    # Security check - only the creator can review
    if listing.user_id != current_user.id:
        flash('You do not have permission to review this listing.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('listing_review.html', listing=listing)

@bp.route('/edit/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def edit(listing_id):
    """Edit existing listing"""
    listing = Item.query.get_or_404(listing_id)
    
    form = postItemForm(obj=listing)
    
    if form.validate_on_submit():
        form.populate_obj(listing)
        listing.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Listing updated successfully!', 'success')
        return redirect(url_for('listings.listing_detail_page', listing_id=listing_id))
    
    return render_template('listing_edit.html', form=form, listing=listing)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/publish/<int:listing_id>', methods=['POST'])
@login_required
def publish(listing_id):
    """Publish the listing"""
    listing = Item.query.get_or_404(listing_id)
    
    if listing.owned_company.id != current_user.owned_company.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.index'))
    
    listing.status = 'published'
    listing.default_image_used = not listing.images  # Set to False if images exist
    
    # Update company stats
    #listing.company.total_listings += 1
    #isting.company.active_listings += 1
    
    db.session.commit()
    
    # Clear from session
    session.pop('pending_listing_id', None)
    
    flash('Your listing is now live!', 'success')
    return redirect(url_for('listings.listing_detail_page', listing_id=listing_id))

@bp.route("/<int:listing_id>",methods=['GET','POST'])
def detail(listing_id):
    listing=Item.query.filter_by(id=listing_id).first()
    form=makeOfferForm()
    now = datetime.now()
        # Increment view count
    listing.views += 1
    db.session.commit()
    
    # Check if listing is expired
    is_expired = listing.expires_at and datetime.utcnow() > listing.expires_at
    
    # Get seller info
    seller = listing.owned_company
    #seller_user = listing.manager
    
    # Get seller stats
    seller_listings_count = Item.query.filter_by(
        company_id=seller.id, 
        status='active'
    ).count()
    
    seller_transactions_count = Transaction.query.filter(
        (Transaction.seller_company_id == seller.id) |
        (Transaction.buyer_company_id == seller.id),
        Transaction.status == 'completed'
    ).count()
    
    seller_rating = seller.rating_avg or 0
    seller_reviews_count = seller.total_reviews or 0
    

    # Get seller reviews (latest 3)
    seller_reviews = Review.query.filter_by(
        company_id=seller.id
    ).order_by(desc(Review.created_at)).limit(3).all()
    
    # Get quality attributes for this listing
    qualities = listing.qualities if hasattr(listing, 'qualities') else []
    # Get current user's pending offer if any
    user_pending_offer = None
    if current_user.is_authenticated:
        user_pending_offer = Offer.query.filter(
            Offer.item_id == listing.id,
            Offer.sender_company_id == current_user.company_id,
            Offer.status == 'pending'
        ).first()
    
    if form.validate_on_submit():
        offer_to_create=Offer(offered_price=form.price.data,
                              quantity_requested=form.quantity.data,
                              message=form.message.data,
                              item_id=request.form['item_id'],
                              buyer_company_id=current_user.company_id,
                              buyer_id=current_user.company_id,
                              sender_company_id=current_user.company_id,
                              seller_id=request.form['seller_id'],
                              seller_company_id=request.form['seller_company_id'],
                              unit=request.form['unit']
                              )
        db.session.add(offer_to_create)
        db.session.commit()

        
        return redirect(url_for("offers_page"))
  
    return render_template('listing_detail.html',listing=listing,form=form,now=now,seller_listings_count=seller_listings_count
                           ,seller_transactions_count=seller_transactions_count,
                           seller_reviews=seller_reviews,
                           seller_rating=seller_rating,
                           seller_reviews_count=seller_reviews_count,seller=seller)
