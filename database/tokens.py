from .db import token_collection


async def is_blacklisted(token: str) -> bool:
    """
    Check if a token is still valid or if it is blacklisted

    :param token: Token to check
    :return: True if token is blacklisted, else False
    """
    db_token = await token_collection.find_one({"token": token})
    if db_token:
        return True
    return False


async def blacklist_token(token: str) -> str:
    """
    Add given token to the blacklist (invalidate it)

    :param token: Token to invalidate
    :return: Database ID of blacklisted token
    """
    db_token = await token_collection.insert_one({"token": token})
    return str(db_token.inserted_id)
