from enum import Enum

from mongoengine import *


class AuthLevel(Enum):
    GUEST = 0
    USER = 1
    ADMIN = 2


class User(Document):
    username = StringField(required=True, unique=True)
    password = StringField(required=True)
    level = EnumField(AuthLevel, default=AuthLevel.USER)


class Flight(Document):
    user = ObjectIdField(required=True)

    date = DateField(required=True, unique=False)
    aircraft = StringField(default="")
    waypoint_from = StringField(default="")
    waypoint_to = StringField(default="")
    route = StringField(default="")

    hobbs_start = DecimalField()
    hobbs_end = DecimalField()
    tach_start = DecimalField()
    tach_end = DecimalField()

    time_start = DateTimeField()
    time_off = DateTimeField()
    time_down = DateTimeField()
    time_stop = DateTimeField()

    time_total = DecimalField(default=0)
    time_pic = DecimalField(default=0)
    time_sic = DecimalField(default=0)
    time_night = DecimalField(default=0)
    time_solo = DecimalField()

    time_xc = DecimalField()
    dist_xc = DecimalField()

    takeoffs_day = IntField()
    landings_day = IntField()
    takeoffs_night = IntField()
    landings_night = IntField()
    landings_all = IntField()

    time_instrument = DecimalField()
    time_sim_instrument = DecimalField()
    holds_instrument = DecimalField()

    dual_given = DecimalField()
    dual_recvd = DecimalField()
    time_sim = DecimalField()
    time_ground = DecimalField()

    tags = ListField(StringField())

    pax = ListField(StringField())
    crew = ListField(StringField())

    comments = StringField()

    photos = ListField(ImageField())
