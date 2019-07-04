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
 
import logging
import ast

import ckan.plugins as plugins
from ckan.plugins import toolkit as toolkit
from ckan.plugins.toolkit import config
from ckanext.csc_report import logic

log = logging.getLogger(__name__)


DEFAULT_RESOURCE_URL_TAG = '/downloads/'

class CscReportException(Exception):
    pass


class CscReportPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurable, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IAuthFunctions, inherit=True)
    plugins.implements(plugins.IActions, inherit=True)


    # ###############################################
    # IConfigurable
    # ###############################################
    def configure(self, config_):
        '''Load config settings for this extension from config file.

        See IConfigurable.

        '''
        if 'googleanalytics.id' not in config_:
            msg = "Missing googleanalytics.id in config"
            log.error(msg)
            raise CscReportException(msg)
        self.googleanalytics_id = config_['googleanalytics.id']
        self.googleanalytics_domain = config_.get(
                'googleanalytics.domain', 'auto')
        self.googleanalytics_fields = ast.literal_eval(config_.get(
            'googleanalytics.fields', '{}'))

        googleanalytics_linked_domains = config_.get(
            'googleanalytics.linked_domains', ''
        )
        self.googleanalytics_linked_domains = [
            x.strip() for x in googleanalytics_linked_domains.split(',') if x
        ]

        if self.googleanalytics_linked_domains:
            self.googleanalytics_fields['allowLinker'] = 'true'

        # If resource_prefix is not in config file then write the default value
        # to the config dict, otherwise templates seem to get 'true' when they
        # try to read resource_prefix from config.
        if 'googleanalytics_resource_prefix' not in config_:
            config_['googleanalytics_resource_prefix'] = (
                    DEFAULT_RESOURCE_URL_TAG)
        self.googleanalytics_resource_prefix = config_[
            'googleanalytics_resource_prefix']

        self.show_downloads = toolkit.asbool(
            config_.get('googleanalytics.show_downloads', True))
        self.track_events = toolkit.asbool(
            config_.get('googleanalytics.track_events', False))


    # ###############################################
    # IConfigurer
    # ###############################################
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')


    # ###############################################
    # IActions
    # ###############################################
    def get_actions(self):
        return {'csc_report_update_published_datasets' : logic.csc_report_update_published_datasets,
                'csc_report_json_published_datasets': logic.csc_report_json_published_datasets,
                'csc_report_json_current_resource_format': logic.csc_report_json_current_resource_format,
                'csc_report_json_current_published_datasets_by_category': logic.csc_report_json_current_published_datasets_by_category,
                'csc_report_json_sessions': logic.csc_report_json_sessions,
                'csc_report_json_visited_datasets': logic.csc_report_json_visited_datasets,
               }

    # ###############################################
    # IAuthFunctions
    # ###############################################
    def get_auth_functions(self):
        return {
            'csc_report_auth': logic.csc_report_auth,
            'csc_report_is_sysadmin_auth': logic.csc_report_is_sysadmin_auth,
            'csc_report_json_published_datasets_auth': logic.csc_report_json_published_datasets_auth,
            'csc_report_json_current_resource_format_auth': logic.csc_report_json_current_resource_format_auth,
            'csc_report_json_current_published_datasets_by_category_auth': logic.csc_report_json_current_published_datasets_by_category_auth,
            'csc_report_json_sessions_auth': logic.csc_report_json_sessions_auth,
            'csc_report_json_visited_datasets_auth': logic.csc_report_json_visited_datasets_auth,
          }
