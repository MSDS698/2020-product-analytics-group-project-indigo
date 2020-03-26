from flask import Flask
from flask import render_template, render_template_string, redirect
from app import application


# @application.route('/')
# @application.route('/index')
# def index():
#     return render_template('index.html')

if __name__ == '__main__':
    application.jinja_env.auto_reload = True
    application.config['TEMPLATES_AUTO_RELOAD'] = True
    application.debug = True
    application.run()
