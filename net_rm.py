from flask import Flask,g, render_template, redirect, url_for, request, abort, make_response
from flask_bootstrap import Bootstrap
import os
import sqlite3
import json
from datetime import datetime
from time import mktime

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'database/data.db'),
    AUTO_DEALLOCATE_TIMEOUT=5400 # Release resource after 1 hour and a half
))

Bootstrap(app)


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    if not hasattr(g,'sqlite_db'):
        g.sqlite_db = connect_db()
    db = g.sqlite_db
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.execute("INSERT INTO journal (event_time, event_action, event_data) VALUES (?, ?, ?)",
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
    cur = db.execute("INSERT INTO resources (resource_name,resource_address,allocated) VALUES (?,?,?)",
                     ["resource1", "192.168.0.1",0])

    cur = db.execute("INSERT INTO journal (event_time, event_action,event_resource_id,event_data) VALUES (?, ?, ?, ?)",
                     [datetime.now(),
                      "ADD_RESOURCE",
                      cur.lastrowid,
                      "Resource added by dummydata!"])
    cur = db.execute("INSERT INTO resources (resource_name,resource_address,allocated) VALUES (?,?,?)",
                     ["resource2", "10.0.0.1",0])
    cur = db.execute(
        "INSERT INTO journal (event_time, event_action,event_resource_id,event_data) VALUES (?, ?, ?, ?)",
        [datetime.now(),
         "ADD_RESOURCE",
         cur.lastrowid,
         "Resource added by dummydata!"])
    db.commit()

def revoke_timedout_allocation(db):
    unixtime = mktime(datetime.now().timetuple())
    unixtime = unixtime - app.config["AUTO_DEALLOCATE_TIMEOUT"]


    for resource in db.execute("SELECT id FROM resources WHERE allocated = 1 AND allocated_at < ?", [unixtime]):
        db.execute("UPDATE resources SET allocated = 0, allocated_to_address = '', allocated_to_id = '', allocated_at = NULL WHERE id = ?",
                   [resource['id']])
        db.execute("INSERT INTO journal (event_time, event_action,event_resource_id,event_data) VALUES (?, ?, ?, ?)",
                   [datetime.now(),
                    "DEALLOCATE_RESOURCE",
                    resource['id'],
                    "Resource deallocated by resource manager"])
    db.commit()


def get_db():
    if not hasattr(g,'sqlite_db'):
        g.sqlite_db = connect_db()
    revoke_timedout_allocation(g.sqlite_db)
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g,'sqlite_db'):
        g.sqlite_db.close()


@app.errorhandler(503)
def custom503(error):
    response = make_response()
    response.status_code = 503
    return response


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


@app.route('/allocate/<type>/to/<requester>', methods=["GET"])
def allocate_resource(type, requester):
    db = get_db()
    cur = db.execute('SELECT * FROM resources WHERE resource_type = ? AND allocated = 0;',
                     [type])
    row = cur.fetchall()

    if len(row) != 0:
        unixtime = mktime(datetime.now().timetuple())
        # update the row in DB to reflect that we are now using the resource
        db.execute("UPDATE resources SET allocated = 1, allocated_to_id = ?, allocated_to_address = ?, allocated_at = ? WHERE id = ?",
                   [   requester,
                       request.remote_addr,
                       unixtime,
                       row[0][0]])

        db.execute("INSERT INTO journal (event_time, event_action,event_resource_id,event_data) VALUES (?, ?, ?, ?)",
                   [datetime.now(),
                    "ALLOCATE_RESOURCE",
                    row[0][0],
                    "Resource allocated to %s for request %s" % (request.remote_addr,requester)])

        db.commit()

        ret = {'id':row[0][0],'address':row[0][2],'name':row[0][1]}
        return json.dumps(ret)
    else:
        abort(503)

@app.route('/deallocate/<id>',methods=["GET"])
def deallocate_resource(id):
    db = get_db()
    db.execute("UPDATE resources SET allocated = 0, allocated_to_address = '', allocated_to_id = '', allocated_at = NULL WHERE id = ?",
                [id])

    db.execute("INSERT INTO journal (event_time, event_action,event_resource_id,event_data) VALUES (?, ?, ?, ?)",
                [datetime.now(),
                 "DEALLOCATE_RESOURCE",
                id,
                 "Resource deallocated by %s" % (request.remote_addr)])

    db.commit()

    return ""

@app.route('/deallocate_ip/<id>',methods=["GET"])
def deallocate_resource_ip(id):
    db = get_db()
    db.execute("UPDATE resources SET allocated = 0, allocated_to_address = '', allocated_to_id = '', allocated_at = NULL WHERE allocated_to_id = ?",
                [id])

    db.execute("INSERT INTO journal (event_time, event_action,event_resource_id,event_data) VALUES (?, ?, ?, ?)",
                [datetime.now(),
                 "DEALLOCATE_RESOURCE (IP)",
                id,
                 "Resource deallocated by %s" % (request.remote_addr)])

    db.commit()

    return ""

@app.route('/add', methods=["POST"])
def add_resource():
    db = get_db()
    cur = db.execute("INSERT INTO resources (resource_name, resource_address, resource_type, allocated) VALUES (?, ?, ?, ?)",
                     [request.form['resource_name'].strip(),
                      request.form['resource_address'].strip(),
                      request.form['resource_type'].strip(),
                      0])
    db.execute("INSERT INTO journal (event_time, event_action,event_resource_id,event_data) VALUES (?, ?, ?, ?)",
               [datetime.now(),
                "ADD_RESOURCE",
                cur.lastrowid,
                "Resource added by %s" % (request.remote_addr)])

    db.commit()
    return redirect(url_for('index'))

@app.route('/remove/<id>', methods=["POST","GET"])
def remove_resource(id):
    db = get_db()
    db.execute("delete from resources where id = ?",(id,))
    db.execute("INSERT INTO journal (event_time, event_action,event_resource_id,event_data) VALUES (?, ?, ?, ?)",
               [datetime.now(),
                "REMOVE_RESOURCE",
                id,
                "Resource removed by %s" % (request.remote_addr)])
    db.commit()
    return redirect(url_for('index'))

@app.route('/')
def index():
    db = get_db()
    cur = db.execute("SELECT * FROM resources")
    entries = cur.fetchall()

    cur = db.execute("SELECT * FROM journal ORDER BY id DESC LIMIT 20")
    events = cur.fetchall()

    return render_template('index.html', resources = entries, events = events)
