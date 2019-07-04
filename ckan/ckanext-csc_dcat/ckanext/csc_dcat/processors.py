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
import argparse
import xml
import json

from ckanext.csc_dcat import helpers as cdh
from rdflib import URIRef, Literal

from ckanext.dcat.utils import dataset_uri, catalog_uri, url_to_rdflib_format


from ckanext.dcat.processors import RDFSerializer, DCAT
from ckanext.dcat.profiles import DCT, XSD

import logging
log = logging.getLogger(__name__)

EXPORT_AVAILABLE_RESOURCE_FORMATS = u'export_available_resource_formats'
EXPORT_AVAILABLE_PUBLISHERS = u'export_available_publishers'
EXPORT_AVAILABLE_THEMES = u'export_available_themes'

class CscRDFSerializer(RDFSerializer):
    '''
    A CKAN to RDF serializer based on rdflib

    Supports different profiles which are the ones that will generate
    the RDF graph.
    '''

    def serialize_catalog(self, catalog_dict=None, dataset_dicts=None,
                          _format='xml', pagination_info=None):
        '''
        Returns an RDF serialization of the whole catalog

        `catalog_dict` can contain literal values for the dcat:Catalog class
        like `title`, `homepage`, etc. If not provided these would get default
        values from the CKAN config (eg from `ckan.site_title`).

        If passed a list of CKAN dataset dicts, these will be also serializsed
        as part of the catalog.
        **Note:** There is no hard limit on the number of datasets at this
        level, this should be handled upstream.

        The serialization format can be defined using the `_format` parameter.
        It must be one of the ones supported by RDFLib, defaults to `xml`.

        `pagination_info` may be a dict containing keys describing the results
        pagination. See the `_add_pagination_triples()` method for details.

        Returns a string with the serialized catalog
        '''

        
        catalog_ref = self.graph_from_catalog(catalog_dict)
        if dataset_dicts:
            i = 0
            publishers = {}
            formats = {}
            themes = cdh.csc_dcat_dict_theme_option_label()
            for dataset_dict in dataset_dicts:
                #Add available resource formats in catalog and publishers
                dataset_dict[EXPORT_AVAILABLE_RESOURCE_FORMATS] = formats
                dataset_dict[EXPORT_AVAILABLE_PUBLISHERS] = publishers
                dataset_dict[EXPORT_AVAILABLE_THEMES] = themes
                dataset_ref = self.graph_from_dataset(dataset_dict)
                publishers = dataset_dict.get(EXPORT_AVAILABLE_PUBLISHERS, {})
                formats = dataset_dict.get(EXPORT_AVAILABLE_RESOURCE_FORMATS, {})
                i = i+1
                self.g.add((catalog_ref, DCAT.dataset, dataset_ref))

            log.debug("[processors] serialize_catalog Total datasets i=%s", i)
            self.g.add((catalog_ref, DCT.extent, Literal(i, datatype=XSD.nonNegativeInteger)))
        
        if pagination_info:
            self._add_pagination_triples(pagination_info)
        
        _format = url_to_rdflib_format(_format)
        output = self.g.serialize(format=_format)

        return output
    
    
    def graph_from_dataset(self, dataset_dict):
        '''
        Given a CKAN dataset dict, creates a graph using the loaded profiles

        The class RDFLib graph (accessible via `serializer.g`) will be updated
        by the loaded profiles.

        Returns the reference to the dataset, which will be an rdflib URIRef.
        '''
        
        dataset_ref = URIRef(self._csc_dataset_uri(dataset_dict))

        for profile_class in self._profiles:
            profile = profile_class(self.g, self.compatibility_mode)
            profile.graph_from_dataset(dataset_dict, dataset_ref)

        return dataset_ref


    def _csc_dataset_uri(self, dataset_dict):
        '''
        Returns an URI for the dataset
    
        This will be used to uniquely reference the dataset on the RDF
        serializations.
    
        The value will be the first found of:
    
            1. `catalog_uri()` + '/catalogo/' + `name` field
            2. The value of the `uri` field
            3. The value of an extra with key `uri`
            4. `catalog_uri()` + '/catalogo/' + `id` field
    
        Check the documentation for `catalog_uri()` for the recommended ways of
        setting it.
    
        Returns a string with the dataset URI.
        '''
    
        if dataset_dict.get('name'):
            uri = '{0}/catalogo/{1}'.format(catalog_uri().rstrip('/'), dataset_dict['name'])
        if not uri:
            uri = dataset_uri(dataset_dict)
        return uri