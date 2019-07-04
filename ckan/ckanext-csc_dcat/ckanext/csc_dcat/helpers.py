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

from ckanext.scheming import helpers as sh
from ckan.plugins.toolkit import get_action

ORG_PROP_ID_UD_ORGANICA = 'C_ID_UD_ORGANICA'

log = logging.getLogger(__name__)

def _csc_dcat_list_dataset_field_labels(name_field=None, value_field=None):
    '''
    Returns the available values that the given dataset name_field may have to the given value_field
    '''
    result = {}
    if name_field is not None:
        dataset = sh.scheming_get_schema('dataset', 'dataset')
        values = sh.scheming_field_by_name(dataset.get('dataset_fields'),
                name_field) or []
        if values and values['choices']:
            for option in values['choices']:
                if option and option['value']:
                    if value_field:
                        if option['value'] == value_field:
                            return {option.get('value'): {'label' : option.get('label'), 'description': option.get('description'), 'dcat_ap': option.get('dcat_ap'), 'notation': option.get('notation')}}
                    else:
                        result[option.get('value')] = {'label' : option.get('label'), 'description': option.get('description'), 'dcat_ap': option.get('dcat_ap'), 'notation': option.get('notation')}
    return result


def _csc_dcat_list_resource_field_values(name_field=None):
    '''
    Returns the available values that the given resource name_field may have
    '''
    result = []
    if name_field is not None:
        dataset = sh.scheming_get_schema('dataset', 'dataset')
        values = sh.scheming_field_by_name(dataset.get('resource_fields'),
                name_field) or []
        if values and values['choices']:
            for option in values['choices']:
                if option and option['value']:
                    result.append(option['value'])
    return result

def csc_dcat_dict_theme_option_label(value=None):
    '''
    Returns available label, descriptions and mappings for theme 
    '''
    result = _csc_dcat_list_dataset_field_labels('theme', value)
    return result

def _csc_dcat_list_format_option_value():
    '''
    Returns available values for format 
    '''
    list = _csc_dcat_list_resource_field_values('format')
    result = {}
    for item in list:
        if item:
            result[item.lower()] = item
    return result

def csc_dcat_organizations_available():
    '''Return a dict of active organizations 
        where key id id_minhap (extra C_ID_UD_ORGANICA value) 
        and value is org_id
    '''
    idminhap_organizations = {}
    context = {'ignore_auth': False}
    data_dict = {'all_fields': True,
                 'include_extras': True}
    organizations = get_action('organization_list')(context, data_dict)
    if organizations:
        idminhap_organizations = {}
        for organization in organizations:
            if organization and organization.get('id', None):
                organization_id = organization.get('id', None)
                organization_name = organization.get('title', None)
                if not organization_name or len(organization_name) == 0:
                    organization_name=organization.get('display_name', '')
                extras = organization.get('extras')
                if organization_id and extras:
                    found = False
                    for extra in extras:
                        if extra and not found:
                            if extra.get('key') == ORG_PROP_ID_UD_ORGANICA:
                                found = True
                                if extra.get('value'):
                                    value = extra.get('value').upper()
                                    if (value not in idminhap_organizations):
                                        idminhap_organizations[value] = [organization_id, organization_name]
                                    else:
                                        log.info("Organization %s[id=%s], the publisher %s is used by other organiztion whose id is %s" %(organization.get('name'), organization.get('id'), publisher, dict_idminhaps.get('value')))
                                break
                    if  not found:
                        log.info("Organization %s[id=%s] has not an extra extra %s or its value is empty" % (organization.get('name'), organization.get('id'), ORG_PROP_ID_UD_ORGANICA))
                else:
                    log.info("Organization %s[id=%s] has not extras" % (organization.get('name'), organization.get('id')))
    log.debug("idminhap_organizations=%s", idminhap_organizations)
    return idminhap_organizations