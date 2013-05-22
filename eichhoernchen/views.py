#!/usr/bin/env python
# encoding: utf-8

from eichhoernchen import app, api
import model

from flask import render_template
from flask import Flask, request
from flask.ext import restful
import flask
import json
import random

import querier

def match_ip_or_403(allowed_ips):
    def decorator(fnct):
        def wrapper(*args, **kwargs):
            if request.remote_addr not in allowed_ips:
                # requester's IP is not in allowed_ips list, 403 - Access denied
                restful.abort(403)
            
            return fnct(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/')
def index():
    return render_template('list.html')

class ObjectSearch(restful.Resource):
    def get(self):
        # Multiple objects aka. search:
        data = []
        
        if 'q' in request.args:
            # TODO: parse argument *q* and use as filter
            q = querier.UserQuery.parse(request.args['q'])
            
            # makeing use of new (full)text index
            # See: http://emptysquare.net/blog/mongodb-full-text-search/
            if q['search']:
                data = model.db.command('text', model.Object.collection_name, 
                    search=q['search'], filter=q['filter'], language=q['language'], limit=q['limit'])
                data = map(lambda x: model.Object.from_pymongo(x['obj']), data['results'])
            else:
                data =  list(model.Object.find(q['filter']).limit(q['limit']))
        else:
            # By default we return the first five objects
            data = list(model.Object.find().limit(5))
        
        # TODO this is a hack: use bson to directly get the dict!
        return map(lambda x: x.to_json(), data)

api.add_resource(ObjectSearch, '/db/obj/search')

class MongoResource(restful.Resource):
    '''Generic restful.Resource for MongoEngine objects.
    Just overwrite *obj* and change allow_change to suite needs.'''
    # This needs to be overwritten by extending classes
    document = None
    
    def load_or_404(self, id_):
        '''Loads Object from database or raises flask 404 exception'''
        
        # Converting string to ObjectId
        if isinstance(id_, basestring):
            try:
                id_ = model.ObjectId(id_)
            except model.InvalidId:
                # id_ is not a real ObjectId
                restful.abort(400)
        
        try:
            return self.document(id_)
        except ValueError:
            # Query returned nothing
            restful.abort(404)
    
    def get(self, id_):
        # Selection of single object by id_
        # TODO this is a hack: use bson to directly get the dict!
        return self.load_or_404(id_).to_json()

    def put(self, id_):
        '''Updates an existing object with *id_*. Or, if *id_* is "new", creates a new object.

        Returns a dictionary with field names as keys and error messages as values.
        If there were no errors, the JSON representation of the object is returned.'''

        # We only respond to valid_ JSON requests that are a dictionary
        if not request.json or type(request.json) is not dict:
            restful.abort(400)
        
        if id_ == "new":
            # Create new Object
            o = self.document()
        else:
            # Update existing Object
            o = self.load_or_404(id_)
        
        err_messages = o.from_json(request.json)
        if err_messages:
            return err_messages

        # Check validity
        err_messages = o.validate()
        if err_messages:
            return err_messages
        
        
        # Do we really want to save changes?
        if 'save' in request.args:
            if not self.allow_change():
                # Change is not allowed -> 403 - Access denied
                restful.abort(403)
            
            # save object
            err_messages = o.save()
            
            if err_messages:
                return err_messages, 400
        
        return o.to_json()
    
    def delete(self, id_):
        '''Deletes an object with *id_*.'''
        if not self.allow_change():
            # Change is not allowed -> 403 - Access denied
            restful.abort(403)
        
        # Selecting object from database and delete
        self.load_or_404(id_).delete()
    
    def allow_change(self):
        '''Is being checked before any changes are made. 
        The changes are only saved if this retruns True.'''
        
        return request.remote_addr == '127.0.0.1'

class ObjectResource(MongoResource):
    document = model.Object
api.add_resource(ObjectResource, '/db/obj/<string:id_>')

class LocationResource(MongoResource):
    document = model.Location
api.add_resource(LocationResource, '/db/loc/<string:id_>')

# class CategoryResource(MongoResource):
#     document = model.Category
# api.add_resource(CategoryResource, '/db/cat/<string:id_>')
# 
# class CompanyResource(MongoResource):
#     document = model.Company
# api.add_resource(CompanyResource, '/db/com/<string:id_>')
# 
# class AttributeResource(MongoResource):
#     document = model.Attribute
# api.add_resource(AttributeResource, '/db/atr/<string:id_>')