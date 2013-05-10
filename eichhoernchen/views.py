#!/usr/bin/env python
# encoding: utf-8

from eichhoernchen import app
from flask import render_template

@app.route('/')
def index():
    return render_template('list.html')