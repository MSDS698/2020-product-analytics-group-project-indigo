#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 17:21:35 2020

@author: hannahlyon
"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'indigo.db')
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:12345678@msds603.c7nyoe5fhgig.us-west-2.rds.amazonaws.com/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SECRET_KEY = os.urandom(24)
