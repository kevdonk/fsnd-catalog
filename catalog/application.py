from flask import Flask, jsonify, request, render_template, url_for, redirect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Stock, Rating

app = Flask(__name__)
engine = create_engine('sqlite:///portfolio.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def findStockByTicker(ticker_symbol):
    return session.query(Stock).filter_by(ticker_symbol=ticker_symbol).one_or_none()


def findRatingByName(rating_name):
    return session.query(Rating).filter_by(name=rating_name).one_or_none()


@app.route('/')
def main():
    return "hi"

#TODO: add JSON endpoint


@app.route('/portfolio')
def viewRatings():
    ratings = session.query(Rating).all()
    return render_template('ratings.html', ratings=ratings)

@app.route('/portfolio/new', methods=['GET', 'POST'])
def newRating():
    if request.method == 'POST':
        rating = Rating(name=request.form['name'])
        session.add(rating)
        session.commit()
        return redirect(url_for('viewRating', rating_name=rating.name))
    else:
        return render_template('newRating.html')

@app.route('/portfolio/<string:rating_name>/stocks')
def viewRating(rating_name):
    rating = findRatingByName(rating_name)
    if rating:
        stocks = session.query(Stock).filter_by(rating_id=rating.id).all()
        return render_template('stocks.html', rating=rating, stocks=stocks)
    else:
        return 'Invalid Rating'


@app.route('/portfolio/<string:rating_name>/new', methods=['GET', 'POST'])
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

@app.route('/portfolio/<string:ticker_symbol>')
def viewStock(ticker_symbol):
    stock = findStockByTicker(ticker_symbol)
    if stock:
        return render_template('stock.html', stock=stock)
    else: 
        return 'Invalid Stock'

@app.route('/portfolio/<string:ticker_symbol>/edit', methods=['GET', 'POST'])
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

@app.route('/portfolio/<string:ticker_symbol>/delete', methods=['GET', 'POST'])
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
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)


