from mongoengine import *

from schemas import AuthLevel


class User(Document):
    username = StringField(required=True, unique=True)
    password = StringField(required=True)

    # EnumField validation is currently broken, replace workaround if MongoEngine is updated to fix it
    level = IntField(choices=[l.value for l in AuthLevel], default=1)
    # level = EnumField(AuthLevel, default=AuthLevel.USER)


class TokenBlacklist(Document):
    token = StringField(required=True)


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
    time_solo = DecimalField(default=0)

    time_xc = DecimalField(default=0)
    dist_xc = DecimalField(default=0)

    takeoffs_day = IntField(default=0)
    landings_day = IntField(default=0)
    takeoffs_night = IntField(default=0)
    landings_night = IntField(default=0)
    landings_all = IntField(default=0)

    time_instrument = DecimalField(default=0)
    time_sim_instrument = DecimalField(default=0)
    holds_instrument = DecimalField(default=0)

    dual_given = DecimalField(default=0)
    dual_recvd = DecimalField(default=0)
    time_sim = DecimalField(default=0)
    time_ground = DecimalField(default=0)

    tags = ListField(StringField())

    pax = ListField(StringField())
    crew = ListField(StringField())

    comments = StringField()

    photos = ListField(ImageField())
