from flask import Flask, jsonify, request, render_template, url_for, redirect, session as login_session, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Stock, Rating

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import httplib2
import json
import random
import requests
import string


app = Flask(__name__)
engine = create_engine('sqlite:///portfolio.db')
Base.metadata.bind = engine

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

DBSession = sessionmaker(bind=engine)
session = DBSession()

def findStockByTicker(ticker_symbol):
    return session.query(Stock).filter_by(ticker_symbol=ticker_symbol).one_or_none()


def findRatingByName(rating_name):
    return session.query(Rating).filter_by(name=rating_name).one_or_none()


@app.route('/')
def main():
    return "hi"


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', state=state)


#JSON routes
@app.route('/portfolio/JSON')
def portfolioJSON():
    portfolio = session.query(Rating).all()
    return jsonify(ratings=[rating.serialize for rating in portfolio])

@app.route('/rating/<string:rating_name>/stocks/JSON')
def ratingStocksJSON(rating_name):
    rating = findRatingByName(rating_name)
    if rating:
        stocks = session.query(Stock).filter_by(rating_id=rating.id).all()
        return jsonify(stocks=[stock.serialize for stock in stocks])
    else:
        return 'Invalid Rating'

@app.route('/stock/<string:ticker_symbol>/JSON')
def stockJSON(ticker_symbol):
    stock = findStockByTicker(ticker_symbol)
    if stock:
        return jsonify(stock=stock.serialize)
    else:
        return 'Invalid Stock'

@app.route('/portfolio')
def viewRatings():
    ratings = session.query(Rating).all()
    return render_template('ratings.html', ratings=ratings)

@app.route('/rating/new', methods=['GET', 'POST'])
def newRating():
    if request.method == 'POST':
        rating = Rating(name=request.form['name'])
        session.add(rating)
        session.commit()
        return redirect(url_for('viewRating', rating_name=rating.name))
    else:
        return render_template('newRating.html')

@app.route('/rating/<string:rating_name>/stocks')
def viewRating(rating_name):
    rating = findRatingByName(rating_name)
    if rating:
        stocks = session.query(Stock).filter_by(rating_id=rating.id).all()
        return render_template('stocks.html', rating=rating, stocks=stocks)
    else:
        return 'Invalid Rating'


@app.route('/rating/<string:rating_name>/new', methods=['GET', 'POST'])
def newStock(rating_name):

    rating = findRatingByName(rating_name)
    if rating:
        if request.method == 'POST':
            stock = Stock(name=request.form['name'], ticker_symbol=request.form['ticker_symbol'], rating_id=rating.id)
            session.add(stock)
            session.commit()
            return redirect(url_for('viewRating', rating_name=rating_name))
        else:
            return render_template('newStock.html', rating_name=rating_name)
    else:
        return 'Invalid Rating'

@app.route('/stock/<string:ticker_symbol>')
def viewStock(ticker_symbol):
    stock = findStockByTicker(ticker_symbol)
    if stock:
        return render_template('stock.html', stock=stock)
    else: 
        return 'Invalid Stock'

@app.route('/stock/<string:ticker_symbol>/edit', methods=['GET', 'POST'])
def editStock(ticker_symbol):
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
            ratings = session.query(Rating).all()
            return render_template('editStock.html', stock=stock, ratings=ratings)
    else:
        return 'Invalid Stock'

@app.route('/stock/<string:ticker_symbol>/delete', methods=['GET', 'POST'])
def deleteStock(ticker_symbol):
    stock = findStockByTicker(ticker_symbol)
    if stock:
        if request.method == 'POST':
            rating = stock.rating
            session.delete(stock)
            session.commit()
            return redirect(url_for('viewRating', rating_name=rating.name))
        else:
            return render_template('deleteStock.html', stock=stock)
    else:
        return 'Invalid Stock'


if __name__ == '__main__':
    app.secret_key = 'hunter2'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)


