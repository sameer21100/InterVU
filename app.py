from flask import Flask, render_template,request, session, flash,redirect,url_for,send_file

from flask_sqlalchemy import SQLAlchemy

app=Flask(__name__)
app.secret_key='123123123123'
