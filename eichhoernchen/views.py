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


def match_ip_or_403(argument):
    def decorator(fnct):
        def wrapper(*args, **kwargs):
            if request.remote_addr not in argument:
                restful.abort(403)
            
            return fnct(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/')
def index():
    return render_template('list.html')

def load_object_or_404(id_):
    '''Loads Object from database or raises flask 404 exception'''
    o = model.Object.objects.with_id(id_)

    if not o:
        restful.abort(404)

    return o

class ObjectSearch(restful.Resource):
    def get(self):
        # Multiple objects aka. search:
        data = []
        
        if 'q' in request.args:
            # TODO: parse argument *q* and use as filter
            return []
        else:
            # By default we return the first five objects
            data = model.Object.objects.limit(5)
        
        # TODO this is a hack: use bson to directly get the dict!
        return json.loads(data.to_json())

api.add_resource(ObjectSearch, '/db/obj/search')

class ObjectUpdate(restful.Resource):
    def get(self, id_):
        # Selection of single object by id_
        # TODO this is a hack: use bson to directly get the dict!
        return json.loads(load_object_or_404(id_).to_json())
    
    
    @match_ip_or_403(['127.0.0.1'])
    def put(self, id_):
        '''Updates an existing object with *id_*. Or, if *id_* is "new", creates a new object.
        
        Returns a dictionary with field names as keys and error messages as values.
        If there were no errors, an empty dictionary is returned.'''
        
        # We only respond to valid_ JSON requests that are a dictionary
        if not request.json or type(request.json) is not dict:
            restful.abort(400)
        
        if id_ == "new":
            # Create new Object
            o = model.Object()
        else:
            # Update existing Object
            o = load_object_or_404(id_)
        
        # update object attributes
        for k,v in request.json.items():
            setattr(o, k, v)
        
        # Check validity or save
        try:
            # Do we really want to save changes?
            if 'save' in request.args:
                # save object (also checks validity)
                o.save()
            else:
                # Check only validity
                o.validate()
        except model.ValidationError as e:
            # Return errors, if they were thrown
            return dict(map(lambda x: (x[0], x[1].message), e.errors.items()))
        
        # If everything is okay, we return no errors:
        return {}
    
    @match_ip_or_403(['127.0.0.1'])
    def delete(self, id_):
        '''Deletes an object with *id_*.'''
        # Selecting object from database and delete
        load_object_or_404(id_).delete()

api.add_resource(ObjectUpdate, '/db/obj/<string:id_>')