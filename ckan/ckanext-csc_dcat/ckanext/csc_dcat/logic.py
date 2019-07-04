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

import datetime
import losser.losser


from ckan.plugins import toolkit
from ckan.plugins.toolkit import config, _
from dateutil.parser import parse as dateutil_parse
from ckanext.dcat.processors import RDFSerializer
from ckanext.csc_dcat.processors import CscRDFSerializer


import logging
log = logging.getLogger(__name__)

DATASETS_PER_PAGE = 500
RDF_FORMAT = 'rdf'

wrong_page_exception = toolkit.ValidationError(
    'Page param must be a positive integer starting in 1')


@toolkit.side_effect_free
def csc_dcat_catalog_show(context, data_dict):
    method_log_prefix = '[%s][csc_dcat_catalog_show]' % __name__
    output = None
    try:
        #log.debug('%s Init method. Inputs context=%s, data_dict=%s' % (method_log_prefix, context, data_dict))
        ini = datetime.datetime.now()
        toolkit.check_access('csc_dcat_catalog_show', context, data_dict)

        page = 1
        data_dict['page'] = page
        limit = data_dict.get('limit', -1)
        _format=data_dict.get('format')
        if _format==RDF_FORMAT:
            filepath = config.get('ckanext.csc_dcat.rdf.filepath', '/tmp/catalog.rdf') 
        else:
            filepath = '/tmp/catalog.' + _format
        query = _csc_dcat_search_ckan_datasets(context, data_dict)
        dataset_dicts = query['results']
        total_datasets = query['count']
        log.debug('%s Total_datasets obtenidos en la query: %s' % (method_log_prefix, total_datasets))
        if limit > -1 and limit < total_datasets:
            total_datasets = limit
        num = len(dataset_dicts)
        log.debug('%s Total_datasets a exportar: %s' % (method_log_prefix, total_datasets))
         
        while (total_datasets > num):
            page = page + 1
            data_dict['page'] = page
            query = _csc_dcat_search_ckan_datasets(context, data_dict)
            dataset_dicts.extend(query['results'])
            total_datasets = query['count']
            num = len(dataset_dicts)
            log.debug('%s Total_datasets obtenidos en la query: %s' % (method_log_prefix, total_datasets))
            log.debug('%s Total_datasets a exportar: %s' % (method_log_prefix, num))

        if _format==RDF_FORMAT:
            serializer = CscRDFSerializer()
            #log.debug("%s DATASET_DICTS = %s" % (method_log_prefix,dataset_dicts))
            output = serializer.serialize_catalog({}, dataset_dicts,
                                              _format=data_dict.get('format'),
                                              pagination_info=None)
            #log.debug('%s Datasets con datos a exportar=%s' % (method_log_prefix, datasets))
            log.debug('%s Numero de datasets con datos a exportar...%s' % (method_log_prefix, num))

        if filepath:
            file = None
            try:
                file = open(filepath, "w")
                file.write(output)
                file.close()
            except:
                if file and not file.closed:
                    file.close()
                
        end = datetime.datetime.now()
        log.debug("%s Time in serialize %s catalog [%s] with %s datasets ... %s milliseconds" % (method_log_prefix, _format, filepath, total_datasets, int((end - ini).total_seconds() * 1000)))
    except Exception, e:
        log.error("%s Exception %s: %s" % (method_log_prefix, type(e).__name__, e))
        output = None
    #log.debug('%s End method. Results = %s' % (method_log_prefix, output))
    log.debug('%s End method.' % (method_log_prefix))
    return output


def _csc_dcat_search_ckan_datasets(context, data_dict):

    method_log_prefix = '[%s][_csc_dcat_search_ckan_datasets]' % __name__
    #log.debug('%s Init method. Inputs context=%s, data_dict=%s' % (method_log_prefix, context, data_dict))
    n = int(config.get('ckanext.dcat.datasets_per_page', DATASETS_PER_PAGE))
    limit = data_dict.get('limit', -1)
    if limit > -1 and limit < n:
        n = limit

    page = data_dict.get('page', 1) or 1
    try:
        page = int(page)
        if page < 1:
            raise wrong_page_exception
    except ValueError:
        raise wrong_page_exception

    modified_since = data_dict.get('modified_since')
    if modified_since:
        try:
            modified_since = dateutil_parse(modified_since).isoformat() + 'Z'
        except (ValueError, AttributeError):
            raise toolkit.ValidationError(
                'Wrong modified date format. Use ISO-8601 format')

    search_data_dict = {
        'rows': n,
        'start': n * (page - 1),
        'sort': 'organization asc, metadata_modified desc',
    }

    search_data_dict['q'] = data_dict.get('q', '*:*')
    search_data_dict['fq'] = data_dict.get('fq')
    search_data_dict['fq_list'] = []

    # Exclude certain dataset types
    search_data_dict['fq_list'].append('-dataset_type:harvest')
    search_data_dict['fq_list'].append('-dataset_type:showcase')

    if modified_since:
        search_data_dict['fq_list'].append(
            'metadata_modified:[{0} TO NOW]'.format(modified_since))

    query = toolkit.get_action('package_search')(context, search_data_dict)

    log.debug('%s End method. Returns query=%s' % (method_log_prefix, query))
    return query


############### AUTHORIZATION ###################

@toolkit.auth_allow_anonymous_access
def csc_dcat_auth(context, data_dict):
    '''
    All users can access DCAT endpoints by default
    '''
    return {'success': True}

def csc_dcat_is_sysadmin(context, data_dict):
    '''
        Only sysadmins can do it
    '''
    if not user_is_sysadmin(context):
        return {'success': False, 'msg': 'Only sysadmins can do this operation'}
    else:
        return {'success': True}

