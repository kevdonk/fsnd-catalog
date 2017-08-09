from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Rating(Base):
    __tablename__ = 'rating'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False, unique=True)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class Stock(Base):
    __tablename__ = 'stock'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    ticker_symbol = Column(String(5), nullable=False, unique=True)
    rating_id = Column(Integer, ForeignKey('rating.id'))
    rating = relationship(Rating)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'ticker_symbol': self.ticker_symbol,
            'rating': self.rating
        }


engine = create_engine('sqlite:///portfolio.db')


Base.metadata.create_all(engine)