#!/bin/bash
set -x
# set -e

# Database, roles, and schema creation
#
# Usage: call with all following env vars
# VAR1=xxx ... VARn=xxx ./create_db.sh


PG_VERSION=9.6
PGHOST=localhost
PGPORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=cenirpostgresql
DB_NAME=nifti2database
DB_SCHEMA=nifti2database_schema
DB_OWNER=nifti2database_owner
DB_OWNER_PASS=nifti2database_owner
DB_APP=nifti2database_app
DB_APP_PASS=nifti2database_app
DB_READ=nifti2database_read
DB_READ_PASS=nifti2database_read


echo "Creating database, schema, and associated roles"
echo "==================================================="


# Check if every needed variable is defined, abort script if not
echo "Using variables:
PGHOST=$PGHOST
PGPORT=$PGPORT
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:0:1}...
DB_SCHEMA=$DB_SCHEMA
DB_NAME=$DB_NAME
DB_OWNER=$DB_OWNER
DB_OWNER_PASS=${DB_OWNER_PASS:0:1}...
DB_APP=$DB_APP
DB_APP_PASS=${DB_APP_PASS:0:1}...
DB_READ=$DB_READ
DB_READ_PASS=${DB_READ_PASS:0:1}..."

if [ -z "$PGHOST" -o \
    -z "$PGPORT" -o \
    -z "$POSTGRES_USER" -o \
    -z "$POSTGRES_PASSWORD" -o \
    -z "$DB_SCHEMA" -o \
    -z "$DB_NAME" -o \
    -z "$DB_OWNER" -o \
    -z "$DB_OWNER_PASS" -o \
    -z "$DB_APP" -o \
    -z "$DB_APP_PASS" -o \
    -z "$DB_READ" -o \
    -z "$DB_READ_PASS" \
     ]; then
     echo "One of the previous variables is not set or empty; please provide all of them  as env vars."
     echo "Aborting database creation..."
     exit 1
fi

PGPASSWORD=${POSTGRES_PASSWORD} psql -U ${POSTGRES_USER} postgres <<EOF

drop database if exists ${DB_NAME};

drop role if exists ${DB_OWNER};
drop role if exists ${DB_APP};
drop role if exists ${DB_READ};

create role ${DB_OWNER} createdb login password '${DB_OWNER_PASS}';
create role ${DB_APP} login password '${DB_APP_PASS}';
create role ${DB_READ} login password '${DB_READ_PASS}';

EOF

if [ $? -ne 0 ]; then
  echo "  => !!! Roles creation didn't go well!"
else
  echo "  => Roles created"
fi

PGPASSWORD=${DB_OWNER_PASS} psql -h localhost -U ${DB_OWNER} postgres <<EOF

create database ${DB_NAME} with encoding='utf8' template=template0;

EOF

if [ $? -ne 0 ]; then
  echo "  => !!! Database creation didn't go well!"
else
  echo "  => Database created"
fi

#PGPASSWORD=${POSTGRES_PASSWORD} psql -U ${POSTGRES_USER} ${DB_NAME} <<EOF
#CREATE EXTENSION IF NOT EXISTS pg_trgm;
#CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
#EOF
#
#if [ $? -ne 0 ]; then
#  echo "  => !!! Extensions creation didn't go well!"
#else
#  echo "  => Extensions created"
#fi

PGPASSWORD=${DB_OWNER_PASS} psql -h localhost -U ${DB_OWNER} ${DB_NAME} <<EOF

begin transaction;

\set ON_ERROR_STOP ON

-- creation du schema principal
drop schema if exists ${DB_SCHEMA} cascade;
create schema ${DB_SCHEMA};

-- privileges sur le schema
grant usage on schema ${DB_SCHEMA} to ${DB_APP}, ${DB_READ};

-- adaptation des privileges par defaut
alter default privileges in schema ${DB_SCHEMA} revoke execute on functions from public;
alter default privileges in schema ${DB_SCHEMA} grant execute on functions to ${DB_APP};
alter default privileges in schema ${DB_SCHEMA} grant all on tables to ${DB_APP};
alter default privileges in schema ${DB_SCHEMA} grant usage on sequences to ${DB_APP};
alter default privileges in schema ${DB_SCHEMA} grant select on tables to ${DB_READ};

commit;

EOF

if [ $? -ne 0 ]; then
  echo "  => !!! Schema creation didn't go well!"
else
  echo "  => Schema created, default privileges set"
fi

PGPASSWORD=${POSTGRES_PASSWORD} psql -U ${POSTGRES_USER} ${DB_NAME} <<EOF

-- search_path
alter role ${DB_OWNER}  set search_path=${DB_SCHEMA},public;
alter role ${DB_APP}  set search_path=${DB_SCHEMA},public;
alter role ${DB_READ}  set search_path=${DB_SCHEMA},public;

EOF

if [ $? -ne 0 ]; then
  echo "  => !!! Search_path definition didn't go well!"
else
  echo "  => Search_path ok"
fi
