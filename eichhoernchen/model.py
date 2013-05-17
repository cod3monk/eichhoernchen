#!/usr/bin/env python
# encoding: utf-8

from mongoengine import *

connect(u'eichhörnchen')

class Location(Document):
    name = StringField(required=True, unique_with='parent', max_length=16)
    parent = ObjectIdField('Location')
    description = StringField()

class Attribute(Document):
    name = StringField(primary_key=True, max_length=8)
    longname = StringField(required=True, max_length=16)
    description = StringField()
    unit = StringField()

class Category(Document):
    title = StringField(required=True, unique_with='parent', max_length=32)
    parent = ObjectIdField('Category')
    children = ListField(ObjectIdField('Category'))
    attributes = ListField(ObjectIdField(Attribute), help_text="These attributes are obligatory "+
        "in this category")
    description = StringField()

class Company(DynamicDocument):
    name = StringField(primary_key=True)
    website = URLField()
    email = EmailField()
    telephone = StringField()

class PurchaseHistory(EmbeddedDocument):
    price = FloatField(required=True)
    quantity = FloatField(required=True, help_text="What quantity does this price apply to, in "+
        "base units?")
    quantity_name = StringField(help_text="Short description of quantity, e.g. '2 qm'.")
    date = DateTimeField(required=True)
    distributer = ObjectIdField(Company)

class Stock(EmbeddedDocument):
    location = ObjectIdField(Location, required=True)
    stock = FloatField(required=True)

class StockHistory(EmbeddedDocument):
    count = FloatField(required=True)
    delta = FloatField(help_text="Delta to live stock value at counting date.")
    date = DateTimeField(required=True)
    location = ObjectIdField(Location, required=True)

class SalePrice(EmbeddedDocument):
    price = FloatField(required=True)
    quantity = FloatField(required=True, help_text="What quantity does this price apply to, in "+
        "base units?")
    sale_unit = StringField(required=True)
    calculation_factor = FloatField(default=1.0, help_text="Used in calculation if purchase "+
        "price changes.")

class Object(DynamicDocument):
    ean = SequenceField(unique=True)
    name = StringField(required=True, max_length=16, help_text="Short description of object")
    longname = StringField(required=True, max_length=64, help_text="Longer description of object")
    description = StringField(help_text="Lengthy description of object (optional)")
    primary_location = ObjectIdField(Location) # This is also the sale_location
    category = ListField(ObjectIdField(Category))
    comment = StringField()
    
    # The following attributes are needed for consumable objects:
    base_unit = StringField(help_text="What unit is being used for calculations?")
    stocks = ListField(EmbeddedDocumentField(Stock))
    stock_history = ListField(EmbeddedDocumentField(StockHistory))
    quota = FloatField(default=0)
    last_ordered = DateTimeField()
    purchase_history = ListField(EmbeddedDocumentField(PurchaseHistory))
    
    # The following attributes are needed for sellable objects:\
    sale_prices = ListField(EmbeddedDocumentField(SalePrice))
