# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from .routes import charts_blueprint
from flask import Blueprint

blueprint = Blueprint(
    'charts_blueprint',
    __name__,
    url_prefix=''
)
