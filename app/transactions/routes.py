import os
from flask import Blueprint, render_template,request
from app.auth.models import Company, User
from app.listings.models import Category,Item, Quality_attributes
from app.transactions.forms import markInTransitForm
from app.transactions.models import Transaction


from flask_login import login_required,current_user
from sqlalchemy import desc,or_
from datetime import datetime
from app.transactions import bp


@bp.route("/")
def index():
    print('------------------------------')
    transactions=Transaction.query.filter(or_(Transaction.seller_company_id==current_user.id ,Transaction.buyer_company_id==current_user.company_id)).order_by(desc(Transaction.created_at)).all()
    
    return render_template('transactions_index.html',transactions=transactions)


@bp.route("/detail/<int:transaction_id>",methods=['POST','GET'])
def detail(transaction_id):
    transaction=Transaction.query.get_or_404(transaction_id)
    mark_in_transit_form=markInTransitForm()
    if mark_in_transit_form.validate_on_submit() :
        print('------------------------- mar_in_trasit')
        transaction.mark_in_transit()
        
    
    return render_template('transactions_detail.html',transaction=transaction,mark_in_transit_form=mark_in_transit_form)

@bp.route("/confirm/<int:transaction_id>")
def confirm(transaction_id):
    transaction=Transaction.query.get_or_404(transaction_id)
    
    return render_template('transaction_confirm.html',transaction=transaction)

@bp.route("/review/<int:transaction_id>")
def review(transaction_id):
    transaction=Transaction.query.get_or_404(transaction_id)
    
@bp.route("/mark_delivered/<int:transaction_id>")
def mark_delivered(transaction_id):
    transaction=Transaction.query.get_or_404(transaction_id)
    
@bp.route("/mark_picked_up/<int:transaction_id>")
def mark_picked_up(transaction_id):
    transaction=Transaction.query.get_or_404(transaction_id)
    
    