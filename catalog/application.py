from flask import Flask, jsonify, request, render_template, url_for, redirect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Stock, Rating

app = Flask(__name__)
engine = create_engine('sqlite:///portfolio.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
def main():
    return "hi"


@app.route('/ratings/<string:rating_name>/JSON')
def ratingJSON(rating_name):
    rating = session.query(Rating).filter_by(name=rating_name).one_or_none()
    if rating:
        return jsonify(Rating=rating.serialize)
    else:
        return "No rating matching name {}".format(rating_name)


@app.route('/ratings/<string:rating_name>/stocks/JSON')
def stocksWithRatingJSON(rating_name):
    stocks = session.query(Stock).filter_by(rating_name=rating_name).all()
    return jsonify(Stocks=[stock.serialize for stock in stocks])


@app.route('/ratings')
def ratings():
    ratings = session.query(Rating).all()
    return render_template('ratings.html', ratings=ratings)

@app.route('/ratings/new', methods=['GET', 'POST'])
def newRating():
    if request.method == 'POST':
        rating = Rating(name=request.form['name'])
        session.add(rating)
        session.commit()
        return redirect(url_for('rating', rating_name=rating.name))
    else:
        return render_template('newrating.html')

@app.route('/ratings/<string:rating_name>/stocks')
def rating(rating_name):
    rating = session.query(Rating).filter_by(name=rating_name).one_or_none()
    if rating:
        stocks = session.query(Stock).filter_by(rating_id=rating.id).all()
        return render_template('stocks.html', rating=rating, stocks=stocks)
    else:
        return 'Invalid Rating'


@app.route('/ratings/<string:rating_name>/new', methods=['GET', 'POST'])
def newStock(rating_name):

    rating = session.query(Rating).filter_by(name=rating_name).one_or_none()
    if rating:
        if request.method == 'POST':
            stock = Stock(name=request.form['name'], ticker_symbol=request.form['ticker_symbol'], rating_id=rating.id)
            session.add(stock)
            session.commit()
            return redirect(url_for('rating', rating_name=rating_name))
        else:
            return render_template('newstock.html', rating_name=rating_name)
    else:
        return 'Invalid Rating'


if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)


