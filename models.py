import datetime
from peewee import SqliteDatabase, Model, OperationalError, CharField, DateTimeField, IntegerField

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
    os = CharField()
    ifconfig = CharField()
    uname = CharField()
    uid = IntegerField()
    last_checkin = DateTimeField(default=datetime.datetime.now)

    def get_dict(self):
        return dict(id=self.id,
                    uuid=self.uuid,
                    ip_addr=self.ip_addr,
                    uname=self.uname,
                    uid=self.uid,
                    os=self.os,
                    updated=self.last_checkin)

