from flask import Flask,g, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
import os
from os.path import isfile
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'database/data.db')
))

Bootstrap(app)


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.execute("insert into journal (event_time, event_action, event_data) values (?, ?, ?)",
               [datetime.now(),
                "CREATE",
                "Database Initialised!"])
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    init_db()
    print "Database Initialised"


@app.cli.command('dummydata')
def dummydata_command():
    db = get_db()
    cur = db.execute("insert into resources (resource_name,resource_address) values (?,?)",
                     ["resource1", "192.168.0.1"])
    cur = db.execute("insert into resources (resource_name,resource_address) values (?,?)",
                     ["resource2", "10.0.0.1"])
    db.commit()

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

@app.route('/remove/<id>', methods=["POST","GET"])
def remove_resource(id):
    db = get_db()
    db.execute("delete from resources where id = ?",id)
    db.commit()
    return redirect(url_for('index'))

@app.route('/')
def index():
    db = get_db()
    cur = db.execute("select * from resources")
    entries = cur.fetchall()
    return render_template('index.html', resources = entries)



if __name__ == "__main__":
    app.run(debug=True)



