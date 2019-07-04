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

import sys
import datetime

from pprint import pprint
from dateutil.parser import parse as dateutil_parse

from ckan import model
from ckan.plugins import toolkit as toolkit
from ckan.plugins.toolkit import CkanCommand, get_action, ValidationError

class CscDcatCommand(CkanCommand):
    
    '''
    Usage:

      csc_dcat catalog_rdf [{limit_num_datasets}]
        - create a RDF serialization of the catalog. 
          Create a file specified in config property 'ckanext.csc_dcat.rdf.filepath'
          or in '/tmp/catalog.rdf' if not exists the property.
          A limit number of datastets can be specified in args. All datasets by default.

    The commands should be run from the ckanext-csc_dcat directory and expect
    a development.ini file to be present. Most of the time you will
    specify the config explicitly though:

        paster --plugin=ckanext-csc_dcat csc_dcat catalog_rdf [{limit_num_datasets}] -c ../ckan/development.ini

    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 2
    min_args = 0

    def __init__(self,name):

        super(CscDcatCommand,self).__init__(name)

    def command(self):
        method_log_prefix = '[%s][command]' % type(self).__name__
        print "%s Init method. Args=%s" % (method_log_prefix, self.args)
        ini = datetime.datetime.now()
        self._load_config()

        # We'll need a sysadmin user to perform most of the actions
        # We will use the sysadmin site user (named as the site_id)
        context = {'model':model,'session':model.Session,'ignore_auth':True}
        self.admin_user = get_action('get_site_user')(context,{})

        if len(self.args) == 0:
            self.parser.print_usage()
            sys.exit(1)
        cmd = self.args[0]
        if cmd == 'catalog_rdf':
            self.generate_catalog('rdf')
        else:
            print '%s Command %s not recognized' % (method_log_prefix, cmd)

        end = datetime.datetime.now()
        print '%s End method. ...Command total runned time: %s milliseconds' % (method_log_prefix, int((end - ini).total_seconds() * 1000))

    def _load_config(self):
        super(CscDcatCommand, self)._load_config()

    def generate_catalog(self, _format='rdf'):
        method_log_prefix = '[%s][generate_catalog]' % type(self).__name__
        print '%s Init method. Inputs: _format=%s' % (method_log_prefix, _format)
        context = {
                'model':model,
                'session':model.Session,
                'user': self.admin_user['name'],
                'ignore_auth': True,
            }

        if len(self.args) >= 2:
            try:
                _limit = int(float(unicode(self.args[1])))
            except ValueError as e:
                print '%s Please provide the limit of datasets to export' % (method_log_prefix)
                sys.exit(1)
        else:
            _limit = -1

        data_dict = {
            'format': _format,
            'limit': _limit
        }

        catalog = get_action('csc_dcat_catalog_show')(context,data_dict)

        print '%s End method' % (method_log_prefix)