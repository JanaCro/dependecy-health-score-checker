from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Database creation
app = Flask("__main__")
app.config['SECRET_KEY'] = "secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calculator.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#default values
class Parameters(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    parameter_name = db.Column("parameter_name", db.String(100), unique=True)
    weight_fixed = db.Column("weight_fixed", db.Float)
    weight_ai = db.Column("weight_ai", db.Float)
    t1 = db.Column("t1", db.Float)
    t2 = db.Column("t2", db.Float)
    description = db.Column("description", db.String(1_000))
    reasoning = db.Column("reasoning", db.String(1_000))

    def __init__(self, parameter_name, weight_fixed, weight_ai, t1, t2, description, reasoning):
        self.parameter_name = parameter_name
        self.weight_fixed = weight_fixed
        self.weight_ai = weight_ai
        self.t1 = t1
        self.t2 = t2
        self.description = description
        self.reasoning = reasoning

    def __repr__(self):
        return f"-----\n" + \
               f"Parameter ID: {self._id}\n" + \
               f"Name: {self.parameter_name}\n" + \
               f"Weight Fixed: {self.weight_fixed}\n" + \
               f"Weight AI: {self.weight_ai}\n" + \
               f"T1: {self.t1}\n" + \
               f"T2: {self.t2}\n" + \
               f"Description: {self.description}\n" + \
               f"Reasoning: {self.reasoning}"

