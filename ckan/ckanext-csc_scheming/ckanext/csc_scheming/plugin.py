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
 
from ckan import plugins
from ckan.plugins import toolkit
from ckan.lib.plugins import DefaultTranslation

from ckanext.csc_scheming import helpers, validators


class CscSchemingPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IValidators, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.ITranslation, inherit=True)

    # ###############################################
    # IConfigurer
    # ###############################################
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
    
    # ###############################################
    # ITemplateHelpers
    # ###############################################
    def get_helpers(self):
        return {
            'csc_dataset_form_value': helpers.csc_dataset_form_value,
            'csc_dataset_form_lang_and_value': helpers.csc_dataset_form_lang_and_value,
            #'csc_dataset_form_organization_list': helpers.csc_dataset_form_organization_list,
            'csc_multiple_field_required': helpers.csc_multiple_field_required,
            'csc_scheming_language_text': helpers.csc_scheming_language_text,

            }

    # ###############################################
    # IValidators
    # ###############################################
    def get_validators(self):
        return {
            'csc_multilanguage_url': validators.csc_multilanguage_url,
            'csc_uri_text': validators.csc_uri_text,
            'csc_uri_text_output': validators.csc_uri_text_output,
            'csc_date_frequency': validators.csc_date_frequency,
            'csc_date_frequency_output': validators.csc_date_frequency_output,
            'csc_date_period': validators.csc_date_period,
            'csc_date_period_output': validators.csc_date_period_output,
            'csc_multiple_uri_text': validators.csc_multiple_uri_text,
            'csc_multiple_uri_text_output': validators.csc_multiple_uri_text_output,
            'csc_fluent_text': validators.csc_fluent_text,
            'csc_spatial': validators.csc_spatial,
            'csc_spatial_output': validators.csc_spatial_output,
        }