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
import json
import ast
import urllib
import urllib2
import threading
import Queue
import hashlib

from ckan import plugins as plugins
from ckan.plugins import toolkit as toolkit
from ckan.controllers.package import PackageController
from ckan.plugins.toolkit import url_for, redirect_to, request, config, c, h
from routes.mapper import SubMapper, Mapper as _Mapper

log = logging.getLogger(__name__)


DEFAULT_RESOURCE_URL_TAG = '/downloads/'



def _post_analytics(
        user, event_type, request_obj_type, request_function, request_id):

    if config.get('googleanalytics.id'):
        data_dict = {
            "v": 1,
            "tid": config.get('googleanalytics.id'),
            "cid": hashlib.md5(c.user).hexdigest(),
            # customer id should be obfuscated
            "t": "event",
            "dh": c.environ['HTTP_HOST'],
            "dp": c.environ['PATH_INFO'],
            "dr": c.environ.get('HTTP_REFERER', ''),
            "ec": event_type,
            "ea": request_obj_type + request_function,
            "el": request_id,
        }
        CscGAPlugin.analytics_queue.put(data_dict)


def post_analytics_decorator(func):

    def func_wrapper(cls, id, resource_id, filename):
        _post_analytics(
            c.user,
            "CKAN Resource Download Request",
            "Resource",
            "Download",
            resource_id
        )

        return func(cls, id, resource_id, filename)

    return func_wrapper


class CscGAException(Exception):
    pass
    



class AnalyticsPostThread(threading.Thread):
    """Threaded Url POST"""
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # grabs host from queue
            data_dict = self.queue.get()

            data = urllib.urlencode(data_dict)
            log.debug("Sending API event to Google Analytics: " + data)
            # send analytics
            urllib2.urlopen(
                "http://www.google-analytics.com/collect",
                data,
                # timeout in seconds
                # https://docs.python.org/2/library/urllib2.html#urllib2.urlopen
                10)

            # signals to queue job is done
            self.queue.task_done()


class CscGAPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurable, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)

    

    analytics_queue = Queue.Queue()


    # ###############################################
    # IConfigurer
    # ###############################################
    def configure(self, config_):
        '''Load config settings for this extension from config file.

        See IConfigurable.

        '''
        if 'googleanalytics.id' not in config_:
            msg = "Missing googleanalytics.id in config"
            log.error(msg)
            raise CscGAException(msg)
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
        self.ga_send_stats = toolkit.asbool(config_.get('ckanext.csc_ga.send_stats', True))

        log.debug('ga_send_stats=%s', self.ga_send_stats)

        toolkit.add_resource('fanstatic', 'csc_ga')

            # spawn a pool of 5 threads, and pass them queue instance
        for i in range(5):
            t = AnalyticsPostThread(self.analytics_queue)
            t.setDaemon(True)
            t.start()



    # ###############################################
    # IConfigurer
    # ###############################################
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')

    def before_map(self, map):
        '''Add new routes that this extension's controllers handle.

        See IRoutes.

        '''
        # Helpers to reduce code clutter
        GET = dict(method=['GET'])
        PUT = dict(method=['PUT'])
        POST = dict(method=['POST'])
        DELETE = dict(method=['DELETE'])
        GET_POST = dict(method=['GET', 'POST'])
        # intercept API calls that we want to capture analytics on
        register_list = [
            'package',
            'dataset',
            'resource',
            'tag',
            'group',
            'related',
            'revision',
            'licenses',
            'rating',
            'user',
            'activity'
        ]
        register_list_str = '|'.join(register_list)
        # /api ver 3 or none
        with SubMapper(map, controller='ckanext.csc_ga.controller:CscGAApiController', path_prefix='/api{ver:/3|}',
                    ver='/3') as m:
            m.connect('/action/{logic_function}', action='action',
                      conditions=GET_POST)

        # /api ver 1, 2, 3 or none
        with SubMapper(map, controller='ckanext.csc_ga.controller:CscGAApiController', path_prefix='/api{ver:/1|/2|/3|}',
                       ver='/1') as m:
            m.connect('/search/{register}', action='search')

        # /api/rest ver 1, 2 or none
        with SubMapper(map, controller='ckanext.csc_ga.controller:CscGAApiController', path_prefix='/api{ver:/1|/2|}',
                       ver='/1', requirements=dict(register=register_list_str)
                       ) as m:

            m.connect('/rest/{register}', action='list', conditions=GET)
            m.connect('/rest/{register}', action='create', conditions=POST)
            m.connect('/rest/{register}/{id}', action='show', conditions=GET)
            m.connect('/rest/{register}/{id}', action='update', conditions=PUT)
            m.connect('/rest/{register}/{id}', action='update', conditions=POST)
            m.connect('/rest/{register}/{id}', action='delete', conditions=DELETE)

        return map

    def after_map(self, map):
        '''Add new routes that this extension's controllers handle.

        See IRoutes.

        '''
        self.modify_resource_download_route(map)
        map.redirect("/analytics/package/top", "/analytics/dataset/top")
        map.connect(
            'analytics', '/analytics/dataset/top',
            controller='ckanext.csc_ga.controller:CscGAController',
            action='view'
        )
        return map

    def modify_resource_download_route(self, map):
        '''Modifies resource_download method in related controller
        to attach GA tracking code.
        '''

        if '_routenames' in map.__dict__:
            if 'resource_download' in map.__dict__['_routenames']:
                route_data = map.__dict__['_routenames']['resource_download'].__dict__
                route_controller = route_data['defaults']['controller'].split(
                    ':')
                module = importlib.import_module(route_controller[0])
                controller_class = getattr(module, route_controller[1])
                controller_class.resource_download = post_analytics_decorator(
                    controller_class.resource_download)
            else:
                # If no custom uploader applied, use the default one
                PackageController.resource_download = post_analytics_decorator(
                    PackageController.resource_download)

    

    def get_helpers(self):
        '''Return the CKAN 2.0 template helper functions this plugin provides.

        See ITemplateHelpers.

        '''
        return {'csc_ga_googleanalytics_header': self.csc_ga_googleanalytics_header,
                'csc_ga_send_stats': self.csc_ga_send_stats}

    def csc_ga_googleanalytics_header(self):
        '''Render the googleanalytics_header snippet for CKAN 2.0 templates.

        This is a template helper function that renders the
        googleanalytics_header jinja snippet. To be called from the jinja
        templates in this extension, see ITemplateHelpers.

        '''
        data = {
            'googleanalytics_id': self.googleanalytics_id,
            'googleanalytics_domain': self.googleanalytics_domain,
            'googleanalytics_fields': str(self.googleanalytics_fields),
            'googleanalytics_linked_domains': self.googleanalytics_linked_domains
        }
        return toolkit.render_snippet(
            'googleanalytics/snippets/csc_googleanalytics_header.html', data)

    def csc_ga_send_stats(self):
        return self.ga_send_stats
