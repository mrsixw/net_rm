
drop table if EXISTS  resources;

create table resources (

  id INTEGER PRIMARY KEY AUTOINCREMENT
  , resource_name TEXT NOT NULL
  , resource_address TEXT NOT NULL
  , allocated INTEGER
  , allocated_to_id TEXT
  , allocated_to_address TEXT

);
