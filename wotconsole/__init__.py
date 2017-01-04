r'''
Wrapper for WarGaming's Console API
'''

import requests

#: Base URL for WG's Console API
api_url = 'https://api-{}-console.worldoftanks.com/wotx/'

# Accounts


def player_search(search, application_id, fields=None, limit=None, stype=None,
                  language='en', api_realm='xbox', timeout=10):
    r'''
    Search for a player by name

    :param str search: Player name to search for. Maximum length is 24 symbols
    :param str application_id: Your application key (generated by WG)
    :param fields: Reponse fields to exclude or _only_ include. To exclude a
                   field, use "-" in front of its name
    :type fields: list(str)
    :param limit: Number of returned entries. Default is 100; values
                      less than 1 or greater than 100 are ignored
    :type limit: int or str
    :param str stype: Search type. Defines minimum length and type of search.
                     Default value is "startswith". Valid values:
                        - "startswith": search by initial characters of player
                                         name. Minimum length: 3 characters.
                                         Case insensitive.
                        - "exact": Search by exact match of player name.
                                    Minimum length: 1 character. Case
                                    insensitive
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'account/list/',
        params={
            'search': search,
            'application_id': application_id,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language,
            'type': stype,
            'limit': limit
        },
        timeout=timeout))


def player_data(account_id, application_id, access_token=None,
                fields=None, language='en', api_realm='xbox', timeout=10):
    r'''
    Retrieve information on one or more players, including statistics. Private
    data requires an access token from a valid, active login.

    :param int account_id: Player ID(s)
    :param str application_id: Your application key (generated by WG)
    :param str access_token: Authentication token from active session
    :param str fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :param str language: Response language
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'account/info/',
        params={
            'account_id': account_id,
            'application_id': application_id,
            'access_token': access_token,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language
        },
        timeout=timeout))


def player_achievements(account_id, application_id, fields=None, language='en',
                        api_realm='xbox', timeout=10):
    r'''
    View player's achievements, such as mastery badges and battle commendations

    :param str account_id
    :param str application_id: Your application key (generated by WG)
    :param str fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :param str language: Response language
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'account/achievements/',
        params={
            'account_id': account_id,
            'application_id': application_id,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language
        },
        timeout=timeout))


def player_data_ps_uid(psnid, application_id, timeout=10):
    r'''
    Retrieve player info using PlayStation UID

    :param str psnid: Play Station UID. Max limit is 100
    :param str application_id: Your application key (generated by WG)
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format('ps4') + 'account/psninfo/',
        params={
            'psnid': psnid,
            'application_id': application_id
        },
        timeout=timeout))


def player_data_xbox_uid(xuid, application_id, timeout=10):
    r'''
    Retrieve player info using Microsoft XUID

    :param str xuid: Player Microsoft XUID. Max limit is 1000
    :param str application_id: Your application key (generated by WG)
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format('xbox') + 'account/xuidinfo/',
        params={
            'xuid': xuid,
            'application_id': application_id
        },
        timeout=timeout))


# Authentication

def player_sign_in(application_id, display=None, expires_at=None,
                   nofollow=None, redirect_uri=None, language='en',
                   api_realm='xbox', timeout=10):
    r'''
    Log in a player, receiving an access token once completed successfully.

    :param str application_id: Your application key (generated by WG)
    :param str display: Layout for mobile applications.
                        Valid values: - "page" - Page
                                      - "popup" - Popup window
                                      - "touch" - Touch
    :param int expires_at: UNIX POSIX timestamp or delta in seconds. Maximum
                           expiration time is 2 weeks
    :param int nofollow: If set to 1, the user is not redirected. A URL is
                         returned in response. Default is 0. Max is 1, Min is 0
    :param HTTP redirect_uri: URL where user is redirected to
    :param str language: Response language
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'auth/login/',
        params={
            'application_id': application_id,
            'display': display,
            'expires_at': expires_at,
            'nofollow': nofollow,
            'redirect_uri': redirect_uri,
            'language': language
        },
        timeout=timeout))


def extend_player_sign_in(access_token, application_id, expires_at=None,
                          api_realm='xbox', timeout=10):
    r'''
    Extend the active session of a user when the current session is about to
    expire

    :param str access_token: Current user active session token
    :param str application_id: Your application key (generated by WG)
    :param int expires_at: UNIX POSIX timestamp or delta in seconds. Maximum
                           expiration time is 2 weeks
    :param str language: Response language
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'auth/prolongate/',
        params={
            'access_token': access_token,
            'application_id': application_id,
            'expires_at': expires_at
        },
        timeout=timeout))


def player_sign_out(access_token, application_id,
                    api_realm='xbox', timeout=10):
    r'''
    Terminate the user's active session. Once successful, the access token will
    no longer be valid

    :param str access_token: Session token for the user
    :param str application_id: Your application key (generated by WG)
    :param str language: Response language
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'auth/logout/',
        params={
            'access_token': access_token,
            'application_id': application_id
        },
        timeout=timeout))


# Clans

def clan_search(application_id, fields=None, limit=None, page_no=None,
                search=None, api_realm='xbox', timeout=10):
    r'''
    Search for clan(s)

    Specifying a clan is _optional._ If you do not specify one, the API will
    simply return a listing of clans in order of highest member count

    :param str application_id: Your application key (generated by WG)
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param int limit: Maximum number of clans to return. Max is 100
    :param int page_no: Page number to start listing on. Default is 1
    :param str search: Clan name to search for
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(api_url.format(api_realm) + 'clans/list/',
                                     params={
        'application_id': application_id,
        'fields': fields if _not_iter(fields) else ','.join(map(str, fields)),
        'limit': limit,
        'page_no': page_no,
        'search': search
    },
        timeout=timeout))


def clan_details(clan_id, application_id, extra=None,
                 fields=None, api_realm='xbox', timeout=10):
    r'''
    Retrieve detailed information on a clan.

    May also be used for retrieving a list of players in a clan.

    :param int clan_id: Clan ID. Min value is 1
    :param str application_id: Your application key (generated by WG)
    :param extra: Extra fields to be included in the response
    :type extra: list(str)
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(api_url.format(api_realm) + 'clans/info/',
                                     params={
        'clan_id': clan_id,
        'application_id': application_id,
        'extra': extra if _not_iter(extra) else ','.join(map(str, extra)),
        'fields': fields if _not_iter(fields) else ','.join(map(str, fields))
    },
        timeout=timeout))


def player_clan_data(clan_id, application_id, extra=None,
                     fields=None, api_realm='xbox', timeout=10):
    r'''
    Retrieve player's clan relationship

    :param str account_id: Player ID number
    :param str application_id: Your application key (generated by WG)
    :param extra: Additional fields to retrieve
    :type extra: list(str)
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'clans/accountinfo/',
        params={
            'clan_id': clan_id,
            'application_id': application_id,
            'extra': extra if _not_iter(extra) else ','.join(map(str, extra)),
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields))
        },
        timeout=timeout))


def clan_glossary(application_id, fields=None, language='en', api_realm='xbox',
                  timeout=10):
    r'''
    Retrieve general information regarding clans (_not_ clan-specific info)

    :param str application_id: Your application key (generated by WG)
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param str language: Response language
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'clans/glossary/',
        params={
            'application_id': application_id,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language
        },
        timeout=timeout))


# Tankopedia

def crew_info(application_id, fields=None, language='en', api_realm='xbox',
              timeout=10):
    r'''
    Retrieve information about crews

    :param str application_id: Your application key (generated by WG)
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param str language: Response language
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'encyclopedia/crewroles/',
        params={
            'application_id': application_id,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language
        },
        timeout=timeout))


def vehicle_info(application_id, fields=None, language='en', nation=None,
                 tank_id=None, tier=None, api_realm='xbox', timeout=10):
    r'''
    Retrieve information on one or more tanks

    :param str application_id: Your application key (generated by WG)
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param str language: Response language
    :param nation: Nation(s) to filter tanks to
    :type nation: list(str)
    :param tank_id: All desired tanks (limit 100)
    :type tank_id: list(int or str)
    :param tier: Tiers to filter to
    :type tier: list(int)
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: Tank information
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'encyclopedia/vehicles/',
        params={
            'application_id': application_id,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language,
            'nation': nation if _not_iter(
                fields) else ','.join(map(str, nation)),
            'tank_id': tank_id if _not_iter(
                tank_id) else ','.join(map(str, tank_id)),
            'tier': tier if _not_iter(tier) else ','.join(map(str, tier))
        },
        timeout=timeout))


def packages_info(tank_id, application_id, fields=None,
                  language='en', api_realm='xbox', timeout=10):
    r'''
    Retrieve package characteristics and their interdependence

    :param tank_id: Vehicle(s) to retireve information for
    :type tank_id: list(int)
    :param str application_id: Your application key (generated by WG)
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param str language: Response language
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'encyclopedia/vehiclepackages/',
        params={
            'tank_id': tank_id if _not_iter(
                tank_id) else ','.join(map(str, tank_id)),
            'application_id': application_id,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language
        },
        timeout=timeout))


def equipment_consumable_info(tank_id, application_id, fields=None,
                              language='en', api_realm='xbox', timeout=10):
    r'''
    Retrieve vehicle equipment and consumables

    :param tank_id: Vehicle(s) to retireve information for
    :type tank_id: list(int)
    :param str application_id: Your application key (generated by WG)
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param str language: Response language
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'encyclopedia/vehicleupgrades/',
        params={
            'tank_id': tank_id if _not_iter(
                tank_id) else ','.join(map(str, tank_id)),
            'application_id': application_id,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language
        },
        timeout=timeout))


def achievement_info(application_id, category=None, fields=None, language='en',
                     api_realm='xbox', timeout=10):
    r'''
    Retrieve list of awards, medals, and ribbons

    :param str application_id: Your application key (generated by WG)
    :param category: Filter by award category. Valid values:
                     - "achievements" - Achievements
                     - "ribbons" - Ribbons
                     Max limit is 100
    :type category: list(str)
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param str language: Response language
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'encyclopedia/achievements/',
        params={
            'application_id': application_id,
            'category': category,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language
        },
        timeout=timeout))


def tankopedia_info(application_id, fields=None, language='en',
                    api_realm='xbox', timeout=10):
    r'''
    Retrieve information regarding the Tankopeida itself

    :param str application_id: Your application key (generated by WG)
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param str language: Response language
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'encyclopedia/info/',
        params={
            'application_id': application_id,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language
        },
        timeout=timeout))


# Player ratings

def types_of_ratings(application_id, fields=None, language='en',
                     platform=None, api_realm='xbox', timeout=10):
    r'''
    Retrieve dictionary of rating periods and ratings details

    :param str application_id: Your application key (generated by WG)
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param str language: Response language
    :param str platform: Console platform. Default is "default" (all consoles).
                         Valid responses:
                         - "default" - All platforms (default)
                         - "xbox" - XBOX
                         - "ps4" - PlayStation 4
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'ratings/types/',
        params={
            'application_id': application_id,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'platform': platform,
            'language': language
        },
        timeout=timeout))


def dates_with_ratings(rating, application_id, account_id=None, fields=None,
                       language='en', platform=None, api_realm='xbox',
                       timeout=10):
    r'''
    Retrieve dates with available rating data

    :param str rating: Rating period
    :param str application_id: Your application key (generated by WG)
    :param account_id: Player account ID. Max limit is 100
    :type account_id: list(int)
    :param str language: Response language
    :param str platform: Console platform. Default is "default" (all consoles).
                         Valid responses:
                         - "default" - All platforms (default)
                         - "xbox" - XBOX
                         - "ps4" - PlayStation 4
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'ratings/dates/',
        params={
            'rating': rating,
            'application_id': application_id,
            'account_id': account_id,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language,
            'platform': platform
        },
        timeout=timeout))


# TODO: Accept `time`/`datetime` timestamp for `date` parameter
def player_ratings(rating, account_id, application_id, date=None, fields=None,
                   language='en', platform=None, api_realm='xbox', timeout=10):
    r'''
    Retrieve player ratings by specified IDs

    :param str rating: Rating period
    :param account_id: Player account ID. Max limit is 100
    :type account_id: list(int)
    :param str application_id: Your application key (generated by WG)
    :param date: Ratings calculation date. Up to 7 days before the current
                 date. Default value: yesterday. Date in UNIX timestamp or ISO
                 8601 format. E.g. 1376542800 or 2013-08-15T00:00:00
    :param str language: Response language
    :param str platform: Console platform. Default is "default" (all consoles).
                         Valid responses:
                         - "default" - All platforms (default)
                         - "xbox" - XBOX
                         - "ps4" - PlayStation 4
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'ratings/accounts/',
        params={
            'rating': rating,
            'account_id': account_id if _not_iter(
                account_id) else ','.join(map(str, account_id)),
            'application_id': application_id,
            'date': date,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'platform': platform,
            'language': language
        },
        timeout=timeout))


def adjacent_positions_in_ratings(
        account_id, rank_field, rating, application_id, date=None,
        fields=None, language='en', limit=None, platform=None,
        api_realm='xbox', timeout=10):
    r'''
    Retrieve list of adjacent positions in specified rating

    :param account_id: Player account ID. Max limit is 100
    :type account_id: list(int)
    :param str rank_field: Rating category
    :param str rating: Rating period
    :param str application_id: Your application key (generated by WG)
    :param date: Ratings calculation date. Up to 7 days before the current
                 date. Default value: yesterday. Date in UNIX timestamp or ISO
                 8601 format. E.g. 1376542800 or 2013-08-15T00:00:00
    :param str language: Response language
    :param int limit: Number of returned entries. Default is 5. Max limit is 50
    :param str platform: Console platform. Default is "default" (all consoles).
                         Valid responses:
                         - "default" - All platforms (default)
                         - "xbox" - XBOX
                         - "ps4" - PlayStation 4
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'ratings/neighbors/',
        params={
            'account_id': account_id,
            'rank_field': rank_field,
            'application_id': application_id,
            'date': date,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language,
            'limit': limit,
            'platform': platform,
        },
        timeout=timeout))


def top_players(rank_field, rating, application_id, date=None, fields=None,
                language='en', limit=None, page_no=None, platform=None,
                api_realm='xbox', timeout=10):
    r'''
    Retrieve the list of top players by specified parameter

    :param str rank_field: Rating category
    :param str rating: Rating period
    :param str application_id: Your application key (generated by WG)
    :param date: Ratings calculation date. Up to 7 days before the current
                 date. Default value: yesterday. Date in UNIX timestamp or ISO
                 8601 format. E.g. 1376542800 or 2013-08-15T00:00:00
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param str language: Response language
    :param int limit: Number of returned entries. Default is 10. Max limit is
                      1000
    :param int page_no: Result page number. Default is 1. Min is 1
    :param str platform: Console platform. Default is "default" (all consoles).
                         Valid responses:
                         - "default" - All platforms (default)
                         - "xbox" - XBOX
                         - "ps4" - PlayStation 4
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'ratings/top/',
        params={
            'rank_field': rank_field,
            'rating': rating,
            'application_id': application_id,
            'date': date,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language,
            'limit': limit,
            'page_no': page_no,
            'platform': platform,
        },
        timeout=timeout))

# Player's vehicles


def player_tank_statistics(account_id, application_id, access_token=None,
                           in_garage=None, fields=None, api_realm='xbox',
                           language='en', tank_id=None, timeout=10):
    r'''
    Retrieve information on all tanks that a player has owned and/or used

    :param int account_id: target player ID
    :param str application_id: Your application key (generated by WG)
    :param str access_token: Authentication token from player login (if
                             accessing private data)
    :param str in_garage: Filter ('0') for tanks absent from garage, or ('1')
                          available
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param str language: Response language
    :param tank_id: Limit statistics to vehicle(s). Max limit is 100
    :type tank_id: list(int)
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'tanks/stats/',
        params={
            'account_id': account_id,
            'application_id': application_id,
            'access_token': access_token,
            'in_garage': in_garage,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'language': language,
            'tank_id': tank_id if _not_iter(
                tank_id) else ','.join(map(str, tank_id))
        },
        timeout=timeout))


def player_tank_achievements(account_id, application_id, access_token=None,
                             fields=None, in_garage=None, tank_id=None,
                             api_realm='xbox', language='en', timeout=10):
    r'''
    Retrieve players' achievement details

    :param int account_id: target player ID
    :param str application_id: Your application key (generated by WG)
    :param str access_token: Authentication token from player login (if
                             accessing private data)
    :param fields: Fields to filter or explicitly include. To exclude,
                       prepend the field with a "-"
    :type fields: list(str)
    :param str in_garage: Filter ('0') for tanks absent from garage, or ('1')
                          available
    :param tank_id: Limit statistics to vehicle(s). Max limit is 100
    :type tank_id: list(int)
    :param str api_realm: Platform API. "xbox" or "ps4"
    :param str language: Response language
    :param int timeout: Maximum allowed time to wait for response from servers
    :returns: API response
    :rtype: WOTXResponse
    :raises WOTXResponseError: If the API returns with an "error" field
    '''
    return WOTXResponse(requests.get(
        api_url.format(api_realm) + 'tanks/achievements/',
        params={
            'account_id': account_id,
            'application_id': application_id,
            'access_token': access_token,
            'fields': fields if _not_iter(
                fields) else ','.join(map(str, fields)),
            'in_garage': in_garage,
            'tank_id': tank_id if _not_iter(
                tank_id) else ','.join(map(str, tank_id)),
            'language': language
        },
        timeout=timeout))


class WOTXResponse(object):
    r'''
    Response wrapper for WG's API
    '''

    def __init__(self, response):
        rjson = response.json()
        if 'data' not in rjson:
            raise WOTXResponseError(rjson, response)
        self.raw = response
        for key, value in rjson.iteritems():
            setattr(self, key, value)

    def __eq__(self, val):
        return 'ok' == val

    def __nonzero__(self):
        return True

    def __len__(self):
        if hasattr(self, 'meta'):
            return self.meta['count']
        return 0

    def __getitem__(self, index):
        return self.data[index]

    def __getattr__(self, unknown):
        try:
            return getattr(self.data, unknown)
        except AttributeError:
            raise TypeError(
                'This instance does not have the attribute \'{}\''.format(
                    unknown))


class WOTXResponseError(Exception):
    r'''
    Error(s) in interaction with WG's API
    '''

    def __init__(self, response, raw):
        super(WOTXResponseError, self).__init__(response['error']['message'])
        self.raw = raw
        for key, value in response.iteritems():
            setattr(self, key, value)

    def __eq__(self, val):
        return 'error' == val

    def __nonzero__(self):
        return False

    def __len__(self):
        return -1

    def __getitem__(self, index):
        return self.error[index]

    def __getattr__(self, unknown):
        try:
            return getattr(self.error, unknown)
        except AttributeError:
            raise TypeError(
                'This instance does not have the attribute \'{}\''.format(
                    unknown))


def _not_iter(item):
    r'''
    Helper function to determine if the object can be iterated over. Used for
    protecting against invalid input by user for parameters than need to be
    `join`'d
    '''
    return item is None or any(isinstance(item, i) for i in [str, int])
