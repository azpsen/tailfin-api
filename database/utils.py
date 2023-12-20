import logging
import os
from datetime import datetime
from functools import reduce

import bcrypt
from fastapi import HTTPException
from mongoengine import DoesNotExist, Q

from database.models import User, AuthLevel, Flight

logger = logging.getLogger("utils")


def update_profile(user_id: str, username: str = None, password: str = None, auth_level: AuthLevel = None):
    """
    Update the profile of the given user

    :param user_id: ID of user to update
    :param username: New username
    :param password: New password
    :param auth_level: New authorization level
    :return: Error message if user not found or access unauthorized, else 200
    """
    try:
        user = User.objects.get(id=user_id)
    except DoesNotExist:
        return {"msg": "user not found"}, 401

    if username:
        existing_users = User.objects(username=username).count()
        if existing_users != 0:
            return {"msg": "Username not available"}
    if auth_level:
        if AuthLevel(user.level) < AuthLevel.ADMIN:
            logger.info("Unauthorized attempt by %s to change auth level", user.username)
            raise HTTPException(403, "Unauthorized attempt to change auth level")

    if username:
        user.update_one(username=username)
    if password:
        hashed_password = bcrypt.hashpw(password.encode('UTF-8'), bcrypt.gensalt())
        user.update_one(password=hashed_password)
    if auth_level:
        user.update_one(level=auth_level)


def create_admin_user():
    """
    Create default admin user if no admin users are present in the database

    :return: None
    """
    if User.objects(level=AuthLevel.ADMIN.value).count() == 0:
        logger.info("No admin users exist. Creating default admin user...")
        try:
            admin_username = os.environ["TAILFIN_ADMIN_USERNAME"]
            logger.info("Setting admin username to 'TAILFIN_ADMIN_USERNAME': %s", admin_username)
        except KeyError:
            admin_username = "admin"
            logger.info("'TAILFIN_ADMIN_USERNAME' not set, using default username 'admin'")
        try:
            admin_password = os.environ["TAILFIN_ADMIN_PASSWORD"]
            logger.info("Setting admin password to 'TAILFIN_ADMIN_PASSWORD'")
        except KeyError:
            admin_password = "admin"
            logger.warning("'TAILFIN_ADMIN_PASSWORD' not set, using default password 'admin'\n"
                           "Change this as soon as possible")
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
        User(username=admin_username, password=hashed_password, level=AuthLevel.ADMIN.value).save()
        logger.info("Default admin user created with username %s",
                    User.objects.get(level=AuthLevel.ADMIN).username)


def get_flight_list(sort: str = None, filters: list[list[dict]] = None, limit: int = None, offset: int = None):
    def prepare_condition(condition):
        field = [condition['field'], condition['operator']]
        field = (s for s in field if s)
        field = '__'.join(field)
        return {field: condition['value']}

    def prepare_conditions(row):
        return (Q(**prepare_condition(condition)) for condition in row)

    def join_conditions(row):
        return reduce(lambda a, b: a | b, prepare_conditions(row))

    def join_rows(rows):
        return reduce(lambda a, b: a & b, rows)

    if sort is None:
        sort = "+date"

    query = join_rows(join_conditions(row) for row in filters)

    if query == Q():
        flights = Flight.objects.all()
    else:
        if limit is None:
            flights = Flight.objects(query).order_by(sort)
        else:
            flights = Flight.objects(query).order_by(sort)[offset:limit]

    return flights


def get_flight_list(sort: str = "date", order: str = "desc", limit: int = None, offset: int = None, user: str = None,
                    date_eq: str = None, date_lt: str = None, date_gt: str = None, aircraft: str = None,
                    pic: bool = None, sic: bool = None, night: bool = None, solo: bool = None, xc: bool = None,
                    xc_dist_gt: float = None, xc_dist_lt: float = None, xc_dist_eq: float = None,
                    instrument: bool = None,
                    sim_instrument: bool = None, dual_given: bool = None,
                    dual_recvd: bool = None, sim: bool = None, ground: bool = None, pax: list[str] = None,
                    crew: list[str] = None, tags: list[str] = None):
    """
    Get an optionally filtered and sorted list of logged flights

    :param sort: Parameter to sort flights by
    :param order: Order of sorting; "asc" or "desc"
    :param limit: Pagination limit
    :param offset: Pagination offset
    :param user: Filter by user
    :param date_eq: Filter by date
    :param date_lt: Get flights before this date
    :param date_gt: Get flights after this date
    :param aircraft: Filter by aircraft
    :param pic: Only include PIC time
    :param sic: Only include SIC time
    :param night: Only include night time
    :param solo: Only include solo time
    :param xc: Only include XC time
    :param xc_dist_gt: Only include flights with XC distance greater than this
    :param xc_dist_lt: Only include flights with XC distance less than this
    :param xc_dist_eq: Only include flights with XC distance equal to this
    :param instrument: Only include instrument time
    :param sim_instrument: Only include sim instrument time
    :param dual_given: Only include dual given time
    :param dual_recvd: Only include dual received time
    :param sim: Only include sim time
    :param ground: Only include ground time
    :param pax: Filter by passengers
    :param crew: Filter by crew
    :param tags: Filter by tags
    :return: Filtered and sorted list of flights
    """
    sort_str = ("-" if order == "desc" else "+") + sort

    query = Q()
    if user:
        query &= Q(user=user)
    if date_eq:
        fmt_date_eq = datetime.strptime(date_eq, "%Y-%m-%d")
        query &= Q(date=fmt_date_eq)
    if date_lt:
        fmt_date_lt = datetime.strptime(date_lt, "%Y-%m-%d")
        query &= Q(date__lt=fmt_date_lt)
    if date_gt:
        fmt_date_gt = datetime.strptime(date_gt, "%Y-%m-%d")
        query &= Q(date__gt=fmt_date_gt)
    if aircraft:
        query &= Q(aircraft=aircraft)
    if pic is not None:
        if pic:
            query &= Q(time_pic__gt=0)
        else:
            query &= Q(time_pic__eq=0)
    if sic is not None:
        if sic:
            query &= Q(time_sic__gt=0)
        else:
            query &= Q(time_sic__eq=0)
    if night is not None:
        if night:
            query &= Q(time_night__gt=0)
        else:
            query &= Q(time_night__eq=0)
    if solo is not None:
        if solo:
            query &= Q(time_solo__gt=0)
        else:
            query &= Q(time_solo__eq=0)
    if xc is not None:
        if xc:
            query &= Q(time_xc__gt=0)
        else:
            query &= Q(time_xc__eq=0)
    if xc_dist_gt:
        query &= Q(dist_xc__gt=xc_dist_gt)
    if xc_dist_lt:
        query &= Q(dist_xc__lt=xc_dist_lt)
    if xc_dist_eq:
        query &= Q(dist_xc__eq=xc_dist_eq)
    if instrument is not None:
        if instrument:
            query &= Q(time_instrument__gt=0)
        else:
            query &= Q(time_instrument__eq=0)
    if sim_instrument is not None:
        if sim_instrument:
            query &= Q(time_sim_instrument__gt=0)
        else:
            query &= Q(time_sim_instrument__eq=0)
    if dual_given is not None:
        if dual_given:
            query &= Q(dual_given__gt=0)
        else:
            query &= Q(dual_given__eq=0)
    if dual_recvd is not None:
        if dual_recvd:
            query &= Q(dual_recvd__gt=0)
        else:
            query &= Q(dual_recvd__eq=0)
    if sim is not None:
        if sim:
            query &= Q(time_sim__gt=0)
        else:
            query &= Q(time_sim__eq=0)
    if ground is not None:
        if ground:
            query &= Q(time_ground__gt=0)
        else:
            query &= Q(time_ground__eq=0)
    if pax:
        query &= Q(pax=pax)
    if crew:
        query &= Q(crew=crew)
    if tags:
        query &= Q(tags=tags)

    if query == Q():
        flights = Flight.objects.all().order_by(sort_str)[offset:limit]
    else:
        flights = Flight.objects(query).order_by(sort_str)[offset:limit]

    return flights
