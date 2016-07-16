# vim: set fileencoding=utf8
# db.py : heroku postgresql connect wrapper
import os
import dj_database_url
import psycopg2
import psycopg2.extras

def connect(url = None):
    if not os.environ.get('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'postgres://vagrant:vagrant@localhost:5432/livechat'
    param =  dj_database_url.config()
    return psycopg2.connect(
            dbname   = param['NAME'],
            user     = param['USER'],
            password = param['PASSWORD'],
            host     = param['HOST'],
            port     = param['PORT'],
            )

def get_dict_cursor(db):
    return db.cursor(cursor_factory=psycopg2.extras.DictCursor)
