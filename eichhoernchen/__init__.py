#!/usr/bin/env python
# encoding: utf-8

from flask import Flask
app = Flask(__name__)

from flask.ext import restful
api = restful.Api(app)

import eichhoernchen.views