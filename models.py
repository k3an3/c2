from peewee import SqliteDatabase, Model, OperationalError, CharField

db = SqliteDatabase('c2.db')


def db_init():
    db.connect()
    try:
        db.create_tables([Zombie])
        print('Creating tables...')
    except OperationalError:
        pass
    db.close()


class BaseModel(Model):
    class Meta:
        database = db


class Zombie(BaseModel):
    uuid = CharField(unique=True)
    ip_addr = CharField()
    sysinfo = CharField()
