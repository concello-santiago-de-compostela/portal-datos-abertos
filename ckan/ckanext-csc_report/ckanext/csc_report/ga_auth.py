#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2018 Ayuntamiento de Santiago de Compostela, Entidad Pública Empresarial Red.es
# 
# This file is part of the "Open Data Portal of Santiago de Compostela", developed within the "Ciudades Abiertas" project.
# 
# Licensed under the EUPL, Version 1.2 or - as soon they will be approved by the European Commission - subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
# 
# https://joinup.ec.europa.eu/software/page/eupl
# 
# Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the Licence for the specific language governing permissions and limitations under the Licence.
 
import httplib2
import logging
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

from pylons import config

log = logging.getLogger(__name__)

def _prepare_credentials(credentials_filename):
    """
    Either returns the user's oauth credentials or uses the credentials
    file to generate a token (by forcing the user to login in the browser)
    """
    scope = ['https://www.googleapis.com/auth/analytics.readonly']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        credentials_filename,
        scopes=scope
    )
    return credentials


def init_service(credentials_file):
    """
    Given a file containing the user's oauth token (and another with
    credentials in case we need to generate the token) will return a
    service object representing the analytics API.
    """
    http = httplib2.Http()

    credentials = _prepare_credentials(credentials_file)
    http = credentials.authorize(http)  # authorize the http object
    
    return build('analytics', 'v3', http=http)


def get_profile_id(service):
    """
    Get the profile ID for this user and the service specified by the
    'googleanalytics.id' configuration option. This function iterates
    over all of the accounts available to the user who invoked the
    service to find one where the account name matches (in case the
    user has several).
    """

    accounts = service.management().accounts().list().execute()

    if not accounts.get('items'):
        return None

    accountName = config.get('googleanalytics.account')
    webPropertyId = config.get('googleanalytics.id')
    for acc in accounts.get('items'):
        if acc.get('name') == accountName:
            accountId = acc.get('id')

    # TODO: check, whether next line is doing something useful.
    webproperties = service.management().webproperties().list(
        accountId=accountId).execute()

    profiles = service.management().profiles().list(
        accountId=accountId, webPropertyId=webPropertyId).execute()

    if profiles.get('items'):
        return profiles.get('items')[0].get('id')

    return None
