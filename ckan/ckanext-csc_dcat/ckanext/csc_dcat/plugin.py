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

from ckanext.csc_dcat import helpers
from ckanext.csc_dcat.logic import (csc_dcat_catalog_show,
                                       csc_dcat_auth,
                                       csc_dcat_is_sysadmin)

class CscDcatPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.ITranslation, inherit=True)
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.IAuthFunctions, inherit=True)

    # ###############################################
    # IConfigurer
    # ###############################################

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'csc_dcat')
    


    # ###############################################
    # ITemplateHelpers
    # ###############################################
    def get_helpers(self):
        return {
            'csc_dcat_dict_theme_option_label': helpers.csc_dcat_dict_theme_option_label,
        }


    # ########################### IActions ####################################
    def get_actions(self):
        return {
            'csc_dcat_catalog_show': csc_dcat_catalog_show,
        }

    # ########################### IAuthFunctions ##############################
    def get_auth_functions(self):
        return {
            'csc_dcat_catalog_show': csc_dcat_auth,
        }