"""Web app to manage a stock portfolio"""
import json
import random
import string
import httplib2
import requests
from flask import Flask, jsonify, request, render_template, url_for, redirect, \
    session as login_session, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Stock, Rating

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

app = Flask(__name__)
engine = create_engine('sqlite:///portfolio.db')
Base.metadata.bind = engine

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

DBSession = sessionmaker(bind=engine)
session = DBSession()

def findStockByTicker(ticker_symbol):
    """Return Stock given ticker_symbol"""
    return session.query(Stock).filter_by(ticker_symbol=ticker_symbol).one_or_none()


def findRatingByName(rating_name):
    """Return Rating given name"""
    return session.query(Rating).filter_by(name=rating_name).one_or_none()

def render_template_with_ratings(*args, **kwargs):
    """Wrapper to pass in ratings and other common vars required by layout template"""
    # generate random 'state' token to verify against
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    ratings = session.query(Rating).all()
    is_logged_in = True
    if 'username' not in login_session:
        is_logged_in = False

    return render_template(args, ratings=ratings, STATE=state, logged_in=is_logged_in, **kwargs)

@app.route('/')
def main():
    """Main just redirects to /portfolio"""
    return redirect('/portfolio')

@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Validate against state token and try to auth through Google"""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    return redirect('/portfolio')


# DISCONNECT - Revoke a current user's token and reset their login_session

@app.route('/gdisconnect')
def gdisconnect():
    """Disconnect from Google auth and clear login_session"""
    access_token = login_session['access_token']
    # handle if user is visiting this page manually without being connected
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
    #clear login_session
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        return redirect('/portfolio')
    else:
        return redirect('/portfolio')

#JSON routes
@app.route('/portfolio/JSON')
def portfolioJSON():
    """Return JSON portfolio"""
    portfolio = session.query(Rating).all()
    return jsonify(ratings=[rating.serialize for rating in portfolio])

@app.route('/rating/<string:rating_name>/stocks/JSON')
def ratingStocksJSON(rating_name):
    """Return JSON stocks"""
    rating = findRatingByName(rating_name)
    if rating:
        stocks = session.query(Stock).filter_by(rating_id=rating.id).all()
        return jsonify(stocks=[stock.serialize for stock in stocks])
    else:
        return 'Invalid Rating'

@app.route('/stock/<string:ticker_symbol>/JSON')
def stockJSON(ticker_symbol):
    """Return JSON single stock"""
    stock = findStockByTicker(ticker_symbol)
    if stock:
        return jsonify(stock=stock.serialize)
    else:
        return 'Invalid Stock'

@app.route('/portfolio')
def viewRatings():
    """'Home' page"""
    return render_template_with_ratings('ratings.html')

@app.route('/rating/new', methods=['GET', 'POST'])
def newRating():
    """Make sure user is logged in, and display page to add new Rating"""
    if 'username' not in login_session:
        return redirect('/portfolio')
    if request.method == 'POST':
        rating = Rating(name=request.form['name'])
        session.add(rating)
        session.commit()
        return redirect(url_for('viewRating', rating_name=rating.name))
    else:
        return render_template_with_ratings('newRating.html')

@app.route('/rating/<string:rating_name>/stocks')
def viewRating(rating_name):
    """Page to view Rating"""
    rating = findRatingByName(rating_name)
    if rating:
        stocks = session.query(Stock).filter_by(rating_id=rating.id).all()
        return render_template_with_ratings('stocks.html', rating=rating, stocks=stocks)
    else:
        return 'Invalid Rating'


@app.route('/rating/<string:rating_name>/new', methods=['GET', 'POST'])
def newStock(rating_name):
    """Make sure user is logged in, and display page to add new Stock"""
    if 'username' not in login_session:
        return redirect('/portfolio')
    rating = findRatingByName(rating_name)
    if rating:
        if request.method == 'POST':
            stock = Stock(name=request.form['name'], ticker_symbol=request.form['ticker_symbol'],\
                rating_id=rating.id)
            session.add(stock)
            session.commit()
            return redirect(url_for('viewRating', rating_name=rating_name))
        else:
            return render_template_with_ratings('newStock.html', rating_name=rating_name)
    else:
        return 'Invalid Rating'

@app.route('/stock/<string:ticker_symbol>')
def viewStock(ticker_symbol):
    """Page to view Stock"""
    stock = findStockByTicker(ticker_symbol)
    if stock:
        return render_template_with_ratings('stock.html', stock=stock)
    else:
        return 'Invalid Stock'

@app.route('/stock/<string:ticker_symbol>/edit', methods=['GET', 'POST'])
def editStock(ticker_symbol):
    """Make sure user is logged in, and display page to edit Stock"""
    if 'username' not in login_session:
        return redirect('/portfolio')
    stock = findStockByTicker(ticker_symbol)
    if stock:
        if request.method == 'POST':
            if request.form['name']:
                stock.name = request.form['name']
            if request.form['ticker_symbol']:
                stock.ticker_symbol = request.form['ticker_symbol']
            if request.form['rating_id']:
                stock.rating_id = request.form['rating_id']

            session.add(stock)
            session.commit()
            return redirect(url_for('viewStock', ticker_symbol=stock.ticker_symbol))
        else:
            return render_template_with_ratings('editStock.html', stock=stock)
    else:
        return 'Invalid Stock'

@app.route('/stock/<string:ticker_symbol>/delete', methods=['GET', 'POST'])
def deleteStock(ticker_symbol):
    """Make sure user is logged in, and display page to delete Stock"""
    if 'username' not in login_session:
        return redirect('/portfolio')
    stock = findStockByTicker(ticker_symbol)
    if stock:
        if request.method == 'POST':
            rating = stock.rating
            session.delete(stock)
            session.commit()
            return redirect(url_for('viewRating', rating_name=rating.name))
        else:
            return render_template_with_ratings('deleteStock.html', stock=stock)
    else:
        return 'Invalid Stock'


if __name__ == '__main__':
    app.secret_key = 'hunter2'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
