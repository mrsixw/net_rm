
drop table if exists  resources;
drop table if exists journal;

create table resources (

  id INTEGER PRIMARY KEY AUTOINCREMENT
  , resource_name TEXT NOT NULL
  , resource_address TEXT NOT NULL
  , resource_type TEXT
  , allocated INTEGER
  , allocated_to_id TEXT
  , allocated_to_address TEXT

);

create table journal (
  id INTEGER PRIMARY KEY AUTOINCREMENT
  , event_time timestamp NOT  NULL
  , event_action text NOT NULL
  , event_resource_id integer
  , event_data text
  , FOREIGN KEY (event_resource_id) REFERENCES resources(id)
);
