#!/usr/bin/env python
""" Database model for the item catalog app"""
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

BASE = declarative_base()


class User(BASE):
    """Table definition for User"""
    __tablename__ = 'user'

    id_user = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    categories = relationship('Category', back_populates='user')
    items = relationship('Item', back_populates='user')

    @property
    def serialize(self):
        """ Return object data in easily serializable format. """
        return {
            'id_user': self.id_user,
            'name': self.name,
            'email': self.email,
            'picture': self.picture
        }


class Category(BASE):
    """Table definition for Category"""
    __tablename__ = 'category'

    id_category = Column(Integer, primary_key=True)
    slug = Column(String(250), nullable=False)
    name = Column(String(250), nullable=False)
    items = relationship('Item', back_populates='category',
                         cascade='delete, delete-orphan')
    id_user = Column(Integer, ForeignKey('user.id_user'))
    user = relationship('User', back_populates='categories')

    @property
    def serialize(self):
        """ Return object data in easily serializable format. """
        return {
            'id_category': self.id_category,
            'slug': self.slug,
            'name': self.name,
            'id_user': self.id_user,
            'items': self.serialize_items,
        }

    @property
    def serialize_items(self):
        """Helper method for serializing items"""
        return [item.serialize for item in self.items]


class Item(BASE):
    """Table definition for Item"""
    __tablename__ = 'item'

    id_item = Column(Integer, primary_key=True)
    id_category = Column(Integer, ForeignKey('category.id_category'),
                         nullable=False)
    image = Column(String(250))
    random_string = Column(String(250))
    slug = Column(String(250), nullable=False)
    name = Column(String(250), nullable=False)
    description = Column(String(250))
    category = relationship('Category', back_populates='items')
    id_user = Column(Integer, ForeignKey('user.id_user'))
    user = relationship('User', back_populates='items')

    @property
    def serialize(self):
        """ Return object data in easily serializable format. """
        return {
            'id_item': self.id_item,
            'id_category': self.id_category,
            'image': self.image,
            'slug': self.slug,
            'name': self.name,
            'description': self.description,
            'id_user': self.id_user,
        }


ENGINE = create_engine('sqlite:///catalog.db')
BASE.metadata.create_all(ENGINE)
