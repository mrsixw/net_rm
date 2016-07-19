from flask import Flask,g, render_template
from flask_bootstrap import Bootstrap
import os
from os.path import isfile
import sqlite3
import json

_SCHEMA="""

create table resources (

  id INTEGER PRIMARY KEY AUTOINCREMENT
  , resource_name TEXT NOT NULL
  , resource_address TEXT NOT NULL
  , allocated INTEGER
  , allocated_to_id TEXT
  , allocated_to_address TEXT

);
"""

app = Flask(__name__)


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g,'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g,'sqlite_db'):
        g.sqlite_db.close()


@app.route('/status', methods=['GET'])
def show_status():
    db = get_db()

    json_ret = dict()

    for resource in db.execute('SELECT * FROM resources'):
        json_ret[resource['id']] = {'id':resource['id'],
                                    'resource_name': resource['resource_name'],
                                    'resource_address': resource['resource_address'],
                                    'allocated': resource['allocated'],
                                    'allocated_to_id': resource['allocated_to_id'],
                                    'allocated_to_address': resource['allocated_to_address']}


    print(json.dumps(json_ret,sort_keys=True, indent=4))
    return json.dumps(json_ret)


@app.route('/allocate')
def allocate_resource():
    pass

@app.route('/deallocate')
def deallocate_resource(resource_address):
    pass


@app.route('/add')
def add_resource():
    pass

@app.route('/remove')
def remove_resource():
    pass

@app.route('/')
def index():
    return render_template('index.html')



def configure_app():
    app.config.from_object(__name__)

    app.config.update(dict(
        DATABASE=os.path.join(app.root_path,'database/data.db')
    ))

    if not isfile(app.config['DATABASE']):
        db = get_db()
        db.executescript(_SCHEMA)

    Bootstrap(app)


if __name__ == "__main__":
    configure_app()
    app.run(debug=True)



