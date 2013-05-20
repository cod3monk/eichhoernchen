#!/usr/bin/env python
# encoding: utf-8

import pymongo
from pymongo import MongoClient
client = MongoClient()
db = client[u'eichhörnchen']

from bson.objectid import ObjectId
from pymongo.errors import InvalidId
from bson import json_util
import json
import re

class Field:
    '''Subclass me to define fields to be used in Documents.'''
    
    def __init__(self, required=False, default=None, unique=False, index=None):
        self.default = default
        self.unique = unique
        self.required = required
    
    def from_json(self, value):
        '''Takes a JSON serializable *value* and returns a pymongo equivilent.
        Inverse of to_json()
        '''
        return value
    
    def to_json(self, value):
        '''Takes a pymongo *value* and returns a json serializable equivilent.
        Inverse of from_json()
        '''
        return value
    
    def _initialize(self, doc, field_name):
        '''Supposed to be called by the surrounding Document.
        Will create the required indices and other "meta" things'''
        
        if self.unique and not self.required:
            doc.collection.ensure_index(field_name, unique=True, sparse=True) # Not yet supported
        elif self.unique and self.required:
            doc.collection.ensure_index(field_name, unique=True)
    
    def check(self, value):
        '''Returns None if *value* is valid, otherwise returns an error message (string).'''
        return None

def MetaDocument(name, bases, dict_):
    '''Making collection_name and collection available before instantization'''
    if 'collection_name' not in dict_:
        dict_['collection_name'] = name
    
    dict_['collection'] = db[dict_['collection_name']]
    
    return type(name, bases, dict_)

class Document:
    '''Subclass me and set the following attributes:
     * collection_name: use this if you want to deviate form the class name (default)
     * fields: are used to convert, validate and initialize the pymongo data
    '''
    fields = {}
    
    __metaclass__ = MetaDocument
    
    @classmethod
    def from_pymongo(cls, data):
        '''Initializes itself from pymongo *data*.'''
        
        inst = cls(_id=None)
        inst.data = data
        return inst
    
    def __init__(self, search=None):
        # This stores the document state and is always compatable for storage
        # (and retreival) by pymongo
        self.data = {}
        
        self.fields['_id'] = ObjectIdField(self.__class__)
        
        for name,field in self.fields.items():
            field._initialize(self, name)
            
            if field.default is not None:
                self.data[name] = field.default
            
        
        # If searc is set, will try to load myself from the database
        if search:
            result = self.find_one(search)
            if not result:
                raise ValueError("Search returned no result.")
            self.data = result.data
        
    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def to_json(self, to_string=False):
        '''Returns a JSON serializable dictionary.
        
        If *to_string* is set, json.dumps will be used to encode to a JSON string first.
        '''
        json_data = self.data
        for key,field in self.fields.items():
            if key in json_data:
                json_data[key] = field.to_json(json_data[key])
        
        if to_string:
            return json.dumps(json_data)
        else:
            return json_data
    
    def from_json(self, json_dict, from_string=False):
        '''Reads in a JSON serializable dictionary *json_dict* and updates itself from it.
        
        If *from_string* is set, json.loads will be used to decode *json_dict* first.
        
        If an error is acountered, an error message dict will be returned and nothing
        gets updated. If everything went smoothly, nothing will be retruned.
        '''
        if from_string:
            json_dict = json.loads(json_dict)
        
        err_msg = {}
        
        for key,field in self.fields.items():
            if key in json_dict:
                try:
                    json_dict[key] = field.from_json(json_dict[key])
                except (ValueError, TypeError) as e:
                    err_msg[key] = e.message
        
        if err_msg:
            return err_msg
        
        self.data.update(json_dict)
    
    def save(self):
        '''Will save Document to database. If this document is new, the '_id' field in 
        data will be set.
        
        Will validate data and return error messages if there have been errors.
        Otherwise returns None.
        '''
        err_msg = self.validate()
        
        try:
            self.collection.save(self.data)
        except pymongo.errors.DuplicateKeyError as e:
            m = re.search(self.collection_name+'\.\$(.+)_[0-9]+', e.message)
            if m:
                err_msg[m.groups()[0]] = "Duplicate key is not allowed."
        
        if err_msg:
            return err_msg
    
    def reload(self):
        '''Updates local data from database, using the '_id' fild in data.
        '''
        self.data = self.collection.find_one(_id)
    
    @classmethod
    def find(cls, *args, **kwargs):
        kwargs['as_class'] = cls
        return cls.collection.find(*args, **kwargs)
    
    @classmethod
    def find_one(cls, *args, **kwargs):
        kwargs['as_class'] = cls
        return cls.collection.find_one(*args, **kwargs)
    
    def validate(self):
        '''Returns a dictionary of validation error messages.'''
        errors = {}
        for name,field in self.fields.items():
            if name in self.data:
                err_msg = field.check(self.data[name])
                if err_msg:
                    errors[name] = err_msg
            elif field.required:
                errors[name] = "Field is required, but nothing was given."
        
        return errors
        
    def has_id(self):
        '''Returns True if data has an '_id' field.
        
        Usually this means, that it is already stored in the database (but not necessarly 
        up-to-date)
        '''
        return '_id' in self.data
    
    def delete(self):
        '''Deletes this document from the database.'''
        if self.has_id():
            return self.collection.remove(self.data['_id'])
        else:
            raise Exception('Document has no \'_id\' field in data. Can not delete.')
        
    def drop_all(self):
        '''Drops all data in the collection behind this document.'''
        self.collection.drop()

class StringField(Field):
    def __init__(self, max_length=None, min_length=None, **kwargs):
        self.max_length = max_length
        self.min_length = min_length
        Field.__init__(self, **kwargs)
        
    def check(self, value):
        # If supperior check failed, return that:
        err_msg = Field.check(self, value)
        if err_msg:
            return err_msg
        
        if self.max_length and self.max_length < len(value):
            return "String is too long. Max. %d characters." % self.max_length
        if self.min_length and self.min_length > len(value):
            return "String is too short. Min. %d characters." % self.max_length

class ObjectIdField(Field):
    def __init__(self, document, **kwargs):
        Field.__init__(self, **kwargs)
        
        if isinstance(document, basestring) or issubclass(document, Document):
            self.document = document
        else:
            raise TypeError("Not of type Document, can not be used as reference.")
        
    def check(self, value):
        if not isinstance(value, ObjectId):
            return "Is not of type ObjectId."
    
    def to_json(self, value):
        return {"$oid": str(value)}
    
    def from_json(self, value):
        if type(value) is not dict or '$oid' not in value:
            raise ValueError("Not a valid BSON ObjectId representation")
        return ObjectId(value["$oid"])
    
    def _initialize(self, doc, field_name):
        Field._initialize(self, doc, field_name)
        
        if isinstance(self.document, basestring):
            if self.document == doc.collection_name:
                self.document = doc
            else:
                raise ValueError("String document can only be of the surrounding Document.")

class Location(Document):
    fields = {'name': StringField(required=True, max_length=16),
              'parent': ObjectIdField('Location')}

class Object(Document):
    fields = {'name': StringField(max_length=16, required=True, unique=True),
              'barcode': StringField(min_length=9, max_length=13, unique=True),
              'description': StringField(),
              'primary_location': ObjectIdField(Location)}

# class Location(Document):
#     name = StringField(required=True, unique_with='parent', max_length=16)
#     parent = ObjectIdField('Location')
#     description = StringField()
# 
# class Attribute(Document):
#     name = StringField(primary_key=True, max_length=8)
#     longname = StringField(required=True, max_length=16)
#     description = StringField()
#     unit = StringField()
# 
# class Category(Document):
#     title = StringField(required=True, max_length=32)
#     parent = ObjectIdField('Category')
#     children = ListField(ObjectIdField('Category'))
#     attributes = ListField(ObjectIdField(Attribute), help_text="These attributes are obligatory "+
#         "in this category")
#     description = StringField()
# 
# class Company(DynamicDocument):
#     name = StringField(unique=True)
#     website = URLField()
#     email = EmailField()
#     telephone = StringField()
# 
# class PurchaseHistory(EmbeddedDocument):
#     price = FloatField(required=True)
#     quantity = FloatField(required=True, help_text="What quantity does this price apply to, in "+
#         "base units?")
#     quantity_name = StringField(help_text="Short description of quantity, e.g. '2 qm'.")
#     date = DateTimeField(required=True)
#     distributer = ObjectIdField(Company)
# 
# class Stock(EmbeddedDocument):
#     location = ObjectIdField(Location, required=True)
#     stock = FloatField(required=True)
# 
# class StockHistory(EmbeddedDocument):
#     count = FloatField(required=True)
#     delta = FloatField(help_text="Delta to live stock value at counting date.")
#     date = DateTimeField(required=True)
#     location = ObjectIdField(Location, required=True)
# 
# class SalePrice(EmbeddedDocument):
#     price = FloatField(required=True)
#     quantity = FloatField(required=True, help_text="What quantity does this price apply to, in "+
#         "base units?")
#     sale_unit = StringField(required=True)
#     calculation_factor = FloatField(default=1.0, help_text="Used in calculation if purchase "+
#         "price changes.")
# 
# class Object(DynamicDocument):
#     barcode = IntField(unique=True)
#     name = StringField(required=True, max_length=16, help_text="Short description of object")
#     longname = StringField(required=True, max_length=64, help_text="Longer description of object")
#     description = StringField(help_text="Lengthy description of object (optional)")
#     primary_location = ObjectIdField(Location) # This is also the sale_location
#     category = ListField(ObjectIdField(Category))
#     comment = StringField()
#     
#     # The following attributes are needed for consumable objects:
#     base_unit = StringField(help_text="What unit is being used for calculations?")
#     stocks = ListField(EmbeddedDocumentField(Stock))
#     stock_history = ListField(EmbeddedDocumentField(StockHistory))
#     quota = FloatField()
#     last_ordered = DateTimeField()
#     purchase_history = ListField(EmbeddedDocumentField(PurchaseHistory))
#     
#     # The following attributes are needed for sellable objects:\
#     sale_prices = ListField(EmbeddedDocumentField(SalePrice))
