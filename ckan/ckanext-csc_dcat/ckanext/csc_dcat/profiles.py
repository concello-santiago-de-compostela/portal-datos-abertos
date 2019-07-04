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

import json
import logging
import sys
import datetime
from dateutil.parser import parse as parse_date_util
from ckanext.scheming import helpers as sh
from ckanext.dcat.profiles import RDFProfile, DCT, DCAT, ADMS, VCARD, FOAF, SCHEMA, LOCN, GSP, OWL, SPDX, GEOJSON_IMT, TIME
from ckanext.dcat.utils import resource_uri, publisher_uri_from_dataset_dict, catalog_uri
from ckanext.csc_dcat import helpers as cdh
from ckanext.csc_dcat.helpers import ORG_PROP_ID_UD_ORGANICA
from rdflib.namespace import Namespace, RDF, XSD, SKOS, RDFS, DC
from rdflib import URIRef, BNode, Literal
from iso8601 import ParseError, parse_date
from pytz import timezone
from pytz.exceptions import AmbiguousTimeError
from ckanext.csc_dcat.processors import EXPORT_AVAILABLE_RESOURCE_FORMATS, EXPORT_AVAILABLE_PUBLISHERS, EXPORT_AVAILABLE_THEMES
from ckan.plugins.toolkit import config, url_for, h

log = logging.getLogger(__name__)

ENCODING = sys.getdefaultencoding()
TIME = Namespace('http://www.w3.org/2006/time#')

namespaces = {
    'dct': DCT,
    'dcat': DCAT,
    'adms': ADMS,
    'vcard': VCARD,
    'foaf': FOAF,
    'schema': SCHEMA,
    'time': TIME,
    'skos': SKOS,
    'locn': LOCN,
    'gsp': GSP,
    'owl': OWL,
    'xsd': XSD
}


#Keys of harvest source config properties
HS_PROP_USER = u'user'
HS_PROP_READ_ONLY = u'read_only'
HS_PROP_DEFULT_CATALOG_LANGUAGE = u'default_catalog_language'
HS_PROP_RDF_FORMAT = u'rdf_format'
#Keys of ckan config properties
CKAN_PROP_LOCALES_OFFERED = u'ckan.locales_offered'
CKAN_PROP_LOCALE_DEFAULT = u'ckan.locale_default'
CKAN_PROP_LOCALE_ORDER = u'ckan.locale_order'
CKAN_PROP_HTTP_PROXY = u'ckanext.csc_dcat.http_proxy'
CKAN_PROP_HTTPS_PROXY = u'ckanext.csc_dcat.https_proxy'

PUBLISHER_PREFIX = u'http://datos.gob.es/recurso/sector-publico/org/Organismo/'
DEFAULT_TIMEZONE = 'Europe/Madrid'
#Keys of catalog dictionary
CAT_ERRORS = u'cat_errors'
CAT_WARNINGS = u'cat_warnings'
CAT_LANGUAGE = u'cat_language'
CAT_TITLE_TRANSLATE = u'cat_title_translated'
CAT_DESCRIPTION = u'cat_description'
CAT_PUBLISHER = u'cat_publisher'
CAT_PUBLISHER_NAME = u'cat_publisher_display_name'
CAT_PUBLISHER_ID_MINHAP = u'cat_publisher_id_minhap'
CAT_SIZE = u'cat_size'
CAT_IDENTIFIER = u'cat_identifier'
CAT_ISSUED_DATE = u'cat_issued_date'
CAT_MODIFIED_DATE = u'cat_modified_date'
CAT_SPATIAL = u'cat_spatial'
CAT_THEME_TAXONOMY = u'cat_theme_taxonomy'
CAT_HOMEPAGE = u'cat_homepage'
CAT_LICENSE = u'cat_license_id'
CAT_URI = u'cat_uri'

#Keys of catalog and dataset dictionary
DS_ERRORS = u'errors'
DS_WARNINGS = u'warnings'
DS_EXTRAS = u'extras'
DS_TAGS = u'tags'
DS_RESOURCES = u'resources'
DS_TYPE = u'type'
DS_ID = u'id'
DS_DEFAULT_CATALOG_LANGUAGE = u'default_catalog_language'
DS_URI = u'uri'
DS_NAME = u'name'
DS_TITLE = u'title'
DS_OWNER_ORG = u'owner_org'
DS_LANGUAGE = u'language'
DS_TITLE_TRANSLATED = u'title_translated'
DS_DESCRIPTION = u'description'
DS_THEME = u'theme'
DS_IDENTIFIER = u'identifier'
DS_ISSUED_DATE = u'issued_date'
DS_MODIFIED_DATE = u'modified_date'
DS_FREQUENCY = u'frequency'
DS_PUBLISHER = u'publisher'
DS_PUBLISHER_NAME = u'publisher_display_name'
DS_PUBLISHER_ID_MINHAP = u'publisher_id_minhap'
DS_LICENSE = u'license_id'
DS_SPATIAL = u'spatial'
DS_TEMPORAL_COVERAGE = u'coverage_new'
DS_VALID = u'valid'
DS_REFERENCE = u'reference'
DS_NORMATIVE = u'conforms_to'
DS_RESOURCE_IDENTIFIER = u'resource_identifier'
DS_RESOURCE_NAME_TRANSLATED = u'name_translated'
DS_RESOURCE_ACCESS_URL = u'url'
DS_RESOURCE_MIMETYPE = u'mimetype'
DS_RESOURCE_FORMAT = u'format'
DS_RESOURCE_BYTE_SIZE = u'byte_size'
DS_RESOURCE_RELATION = u'resource_relation'


class CscDgeProfile(RDFProfile):

    

    def _get_ckan_locales_offered(self):
        ''' Returns locales offered '''
        return config.get(CKAN_PROP_LOCALES_OFFERED, None)
    
    def _get_ckan_default_locale(self):
        ''' Returns default locale '''
        return config.get(CKAN_PROP_LOCALE_DEFAULT, 'es')

    def _add_translated_triple_field_from_dict(self, _dict, subject, predicate, key, fallbacks=None):
        '''
        Adds a new triple to the graph for each language with the provided parameters

        The subject and predicate of the triple are passed as the relevant
        RDFLib objects (URIRef or BNode). The object is always a literal value,
        which is extracted from the dict using the provided key (see
        `_get_dict_value`). If the value for the key is not found, then
        additional fallback keys are checked.
        '''
        value = self._get_dict_value(_dict, key)
        if not value and fallbacks:
            for fallback in fallbacks:
                value = self._get_dict_value(_dict, fallback)
                if value:
                    break

        # List of values
        if isinstance(value, dict):
            items = value
            for k, v in items.items():
                if k and v:
                    self.g.add((subject, predicate, Literal(v, lang=k)))

    def _add_date_triple(self, subject, predicate, value):
        '''
        Adds a new triple with a date object

        Dates are parsed using iso8601, and if the date obtained is correct,
        added to the graph as an XSD.dateTime value.
        All dates are in timezone 'Europe/Madrid'

        If there are parsing errors, the literal string value is added.
        '''
        if not value:
            return
        try:
            default_timezone = timezone(DEFAULT_TIMEZONE)
            naive = parse_date(value, None)
            #FIXME - is_dst a False para evitar AmbiguousTimeError en fechas en que
            # se cambia la hora.
            try:
                local_dt = default_timezone.localize(naive, is_dst=None)
            except AmbiguousTimeError:
                log.info("AmbiguousTimeError - %s", value)
                local_dt = default_timezone.localize(naive, is_dst=False)
            #remove microseconds
            final_local_dt = local_dt.replace(microsecond=0)
            self.g.add((subject, predicate, Literal(final_local_dt.isoformat(),
                                                    datatype=XSD.dateTime)))
        except ParseError:
            self.g.add((subject, predicate, Literal(value)))

    def _add_skos_concept(self, concept=None, value=None, labels=None, descriptions=None, mapping=None, notation=None):
        if concept and value and isinstance(concept, URIRef):
            self.g.add((concept, RDF.type, SKOS.Concept))
            if labels:
                if isinstance(labels, dict):
                    for key, value in labels.items():
                        if value and value != '':
                            self.g.add((concept, SKOS.prefLabel,
                                        Literal(value, lang=key)))
                else:
                    if labels and labels != '':
                        self.g.add((concept, SKOS.prefLabel, Literal(labels)))
            if descriptions:
                if isinstance(descriptions, dict):
                    for key, value in descriptions.items():
                        if value and value != '':
                            self.g.add((concept, SKOS.definition,
                                        Literal(value, lang=key)))
                else:
                    if descriptions and descriptions != '':
                        self.g.add(
                            (concept, SKOS.definition, Literal(descriptions)))
            if mapping:
                self.g.add((concept, SKOS.broadMatch, URIRef(mapping)))
            if notation:
                self.g.add((concept, SKOS.notation, Literal(notation)))

    def _add_resource_list_triple(self, subject, predicate, value, labels=None, descriptions=None, mapping=None, notation=None):
        '''
        Adds as many triples to the graph as values

        Values are literal strings, if `value` is a list, one for each
        item. If `value` is a string there is an attempt to split it using
        commas, to support legacy fields.
        '''
        items = []
        # List of values
        if isinstance(value, list):
            items = value
        elif isinstance(value, basestring):
            try:
                # JSON list
                items = json.loads(value)
            except ValueError:
                if ',' in value:
                    # Comma-separated list
                    items = value.split(',')
                else:
                    # Normal text value
                    items = [value]
        for item in items:
            concept = URIRef(item)
            self.g.add((subject, predicate, concept))
            if labels or descriptions or mapping or notation:
                self._add_skos_concept(
                    concept, value, labels, descriptions, mapping, notation)

    def _get_value_from_dict(self, _dict, key, fallbacks=None):
        '''
        Returns the value for the given key on a CKAN dict

        The subject and predicate of the triple are passed as the relevant
        RDFLib objects (URIRef or BNode). The object is always a literal value,
        which is extracted from the dict using the provided key (see
        `_get_dict_value`). If the value for the key is not found, then
        additional fallback keys are checked.
        '''
        value = self._get_dict_value(_dict, key)
        if not value and fallbacks:
            for fallback in fallbacks:
                value = self._get_dict_value(_dict, fallback)
                if value:
                    break
        return value

    def graph_from_catalog(self, catalog_dict, catalog_ref):
        '''
        Creates an RDF graph for the whole catalog (site)

        The class RDFLib graph (accessible via `self.g`) should be updated on
        this method
            `catalog_dict` is a dict that can contain literal values for the
            dcat:Catalog class like `title`, `homepage`, etc. `catalog_ref` is an
            rdflib URIRef object that must be used to reference the catalog when
            working with the graph.
        '''
        method_log_prefix = '[%s][graph_from_catalog]' % type(self).__name__
        #log.debug('%s Init method. Inputs: catalog_dict=%r, catalog_ref=%r' % (
        #   method_log_prefix, catalog_dict, catalog_ref))
        try:
            self.organizations = {}

            g = self.g

            for prefix, namespace in namespaces.iteritems():
                g.bind(prefix, namespace)

            g.add((catalog_ref, RDF.type, DCAT.Catalog))

           # Languages
            default_locale = self._get_ckan_default_locale()
            locales_offered = self._get_ckan_locales_offered().split()
            if (locales_offered):
                for locale in locales_offered:
                    g.add((catalog_ref, DCT.language, Literal(locale)))

            # Translate fields
            default_title = config.get('ckanext.csc_dcat.catalog.title', None)
            default_description = config.get(
                'ckanext.csc_dcat.catalog.description', None)
            items = [
                ('title', DCT.title, default_title, default_locale),
                ('description', DCT.description,
                 default_description, default_locale)
            ]
            if (locales_offered):
                items = []
                for locale in locales_offered:
                    items.append(('title_' + locale, DCT.title, config.get(
                        'ckanext.csc_dcat.catalog.title_' + locale, default_title), locale))
                    items.append(('description_' + locale, DCT.description, config.get(
                        'ckanext.csc_dcat.catalog.description_' + locale, default_description), locale))

            for item in items:
                key, predicate, fallback, locale = item
                if catalog_dict:
                    value = catalog_dict.get(key, fallback)
                else:
                    value = fallback
                if value:
                    g.add((catalog_ref, predicate, Literal(value, lang=locale)))

            # Basic fields
            items = [
                ('homepage', FOAF.homepage, config.get(
                    'ckanext.csc_dcat.catalog.homepage')),
                ('spatial', DCT.spatial, config.get(
                    'ckanext.csc_dcat.catalog.spatial')),
                ('themeTaxonomy', DCAT.themeTaxonomy, config.get(
                    'ckanext.csc_dcat.catalog.theme_taxonomy')),
                ('license', DCT.license, config.get(
                    'ckanext.csc_dcat.catalog.license')),
                ('publisher', DCT.publisher, config.get(
                    'ckanext.csc_dcat.catalog.publisher'))
            ]

            for item in items:
                key, predicate, fallback = item
                if catalog_dict:
                    value = catalog_dict.get(key, fallback)
                else:
                    value = fallback
                if value:
                    g.add((catalog_ref, predicate, URIRef(value)))

            #publisher
            organizations = cdh.csc_dcat_organizations_available()
            publisher = config.get('ckanext.csc_dcat.catalog.publisher', None)
            if publisher and len(publisher.strip()) > 0:
                publisher = publisher.strip()
                uriref_publisher = URIRef(publisher)
                s_publisher = publisher.upper().split('/')
                if s_publisher and len(s_publisher) > 0:
                    organization_minhap = s_publisher[-1]
                    org = organizations.get(organization_minhap, None)
                    if org:
                        publisher = [org[1], PUBLISHER_PREFIX +
                                     organization_minhap, organization_minhap]
                        self._add_skos_concept(
                            uriref_publisher, s_publisher[1], s_publisher[0], None, None, s_publisher[2])

            # Dates
            modified = self._last_catalog_modification()
            if modified:
                self._add_date_triple(catalog_ref, DCT.modified, modified)

            #Issued
            issued = config.get('ckanext.csc_dcat.catalog.issued', None)
            if issued:
                self._add_date_triple(catalog_ref, DCT.issued, issued)
            catalog_dict[EXPORT_AVAILABLE_RESOURCE_FORMATS] = cdh._csc_dcat_list_format_option_value()
        except Exception, e:
            log.error("%s Unexpected Error %s: %s" %
                      (method_log_prefix, type(e).__name__, e))
        except:
            log.error("%s Unexpected Generic Error" % (method_log_prefix))
        log.debug('%s End method' % (method_log_prefix))

    def graph_from_dataset(self, dataset_dict, dataset_ref):
        '''
        Given a CKAN dataset dict, creates an RDF graph

        The class RDFLib graph (accessible via `self.g`) should be updated on
        this method

        `dataset_dict` is a dict with the dataset metadata like the one
        returned by `package_show`. `dataset_ref` is an rdflib URIRef object
        that must be used to reference the dataset when working with the graph.
        '''
        method_log_prefix = '[%s][graph_from_dataset]' % type(
            self).__name__
        #log.debug('%s Init method. Inputs dataset_dict=%r, dataset_ref=%r' % (method_log_prefix, dataset_dict, dataset_ref))
        #log.debug('%s Init method. Inputs, dataset_ref=%r' % (method_log_prefix, dataset_ref))
        try:
            g = self.g

            for prefix, namespace in namespaces.iteritems():
                g.bind(prefix, namespace)

            g.add((dataset_ref, RDF.type, DCAT.Dataset))

            # Title
            self._add_translated_triple_field_from_dict(
                dataset_dict, dataset_ref, DCT.title, DS_TITLE_TRANSLATED, None)

            # Description
            self._add_translated_triple_field_from_dict(
                dataset_dict, dataset_ref, DCT.description, DS_DESCRIPTION, None)

            # Theme
            value = self._get_dict_value(dataset_dict, DS_THEME)
            if value:
                themes = dataset_dict.get(EXPORT_AVAILABLE_THEMES, {})
                for theme in value:
                    #self._add_resource_list_triple(dataset_ref, DCAT.theme, value)
                    theme_values = themes.get(theme, {})
                    labels = theme_values.get('label')
                    descriptions = theme_values.get('description')
                    dcat_ap = theme_values.get('dcat_ap')
                    notation = theme_values.get('notation')
                    self._add_resource_list_triple(
                        dataset_ref, DCAT.theme, theme, labels, descriptions, dcat_ap, notation)

            # Tags
            for tag in dataset_dict.get('tags', []):
                self.g.add(
                    (dataset_ref, DCAT.keyword, Literal(tag['name'])))

            # Identifier
            self._add_triple_from_dict(
                dataset_dict, dataset_ref, DCT.identifier, DS_IDENTIFIER, None, False, False)

            # Issued, Modified dates
            self._add_date_triple(dataset_ref, DCT.issued, self._get_value_from_dict(
                dataset_dict, DS_ISSUED_DATE, ['metadata_created']))
            self._add_date_triple(dataset_ref, DCT.modified, self._get_value_from_dict(
                dataset_dict, DS_MODIFIED_DATE, ['metadata_modified']))
            self._add_date_triple(dataset_ref, DCT.valid, self._get_value_from_dict(
                dataset_dict, DS_VALID, None))

            # Accrual periodicity
            frequency = dataset_dict.get(DS_FREQUENCY)
            if frequency:
                ftypes = {'seconds': TIME.seconds,
                          'minutes': TIME.minutes,
                          'hours': TIME.hours,
                          'days': TIME.days,
                          'weeks': TIME.weeks,
                          'months': TIME.months,
                          'years': TIME.years}
                ftype = frequency.get('type')
                fvalue = frequency.get('value')
                if ftype and ftype in ftypes.keys() and fvalue:
                    duration = BNode()
                    frequency = BNode()
                    g.add((frequency, RDF.type, DCT.Frequency))
                    g.add((duration, RDF.type, TIME.DurationDescription))
                    g.add((dataset_ref, DCT.accrualPeriodicity, frequency))
                    g.add((frequency, RDF.value, duration))
                    g.add((duration, ftypes.get(ftype), Literal(
                        fvalue, datatype=XSD.decimal)))

            # Languages
            self._add_triple_from_dict(
                dataset_dict, dataset_ref, DCT.language, DS_LANGUAGE, None, True, False)

            # Publisher
            pub_dir3 = False
            publishers = dataset_dict.get(
                EXPORT_AVAILABLE_PUBLISHERS, {})
            organization_id = dataset_dict.get('owner_org')
            if organization_id in publishers:
                publisher = publishers.get(organization_id)
            else:
                org = h.get_organization(organization_id, False)
                publisher = [None, None, None]
                if org:
                    publisher = [org.get('title'), None, None]
                    if org['extras']:
                        for extra in org.get('extras'):
                            if extra and 'key' in extra and extra['key'] == ORG_PROP_ID_UD_ORGANICA:
                                notation = extra.get('value')
                                if notation and notation != '':
                                    pub_dir3 = True
                                    publisher[1] = PUBLISHER_PREFIX + notation
                                    publisher[2] = notation
                if pub_dir3:
                    publishers[organization_id] = publisher
                    dataset_dict[EXPORT_AVAILABLE_PUBLISHERS] = publishers
                else:
                    #publisher 
                    organizations = cdh.csc_dcat_organizations_available()
                    publisher_ref = config.get('ckanext.csc_dcat.catalog.publisher', None)
                    if publisher_ref and len(publisher_ref.strip()) > 0:
                        publisher_ref = publisher_ref.strip()
                        publisher = [publisher_ref, None, None]
                        s_publisher = publisher_ref.upper().split('/')
                        if s_publisher and len(s_publisher) > 0:
                            organization_minhap = s_publisher[-1]
                            org = organizations.get(organization_minhap, None)
                            if org:
                                publisher = [org[1], PUBLISHER_PREFIX +
                                        organization_minhap, organization_minhap]
            if publisher[1]:
                self._add_resource_list_triple(
                        dataset_ref, DCT.publisher, publisher[1], publisher[0], None, None, publisher[2])
            else:
                g.add((dataset_ref, DCT.publisher, URIRef(publisher[0])))

            # Spatial Coverage
            value = self._get_dict_value(dataset_dict, DS_SPATIAL)
            if value:
                self._add_resource_list_triple(
                    dataset_ref, DCT.spatial, value)

            # Temporal
            temporal_coverage = self._get_dataset_value(
                dataset_dict, DS_TEMPORAL_COVERAGE)
            i = 1
            if temporal_coverage:
                for key, value in temporal_coverage.items():
                    if (value):
                        start = end = None
                        if 'from' in value:
                            start = value.get('from')
                        if 'to' in value:
                            end = value.get('to')
                        if start or end:
                            temporal_extent = URIRef(
                                "%s/%s-%s" % (dataset_ref, 'PeriodOfTime', i))
                            g.add(
                                (temporal_extent, RDF.type, DCT.PeriodOfTime))
                            if start:
                                self._add_date_triple(
                                    temporal_extent, SCHEMA.startDate, start)
                            if end:
                                self._add_date_triple(
                                    temporal_extent, SCHEMA.endDate, end)
                            g.add((dataset_ref, DCT.temporal, temporal_extent))
                            i = i+1

            # References
            value = self._get_dict_value(dataset_dict, DS_REFERENCE)
            if value:
                self._add_resource_list_triple(
                    dataset_ref, DCT.references, value)

            # Conforms To
            value = self._get_dict_value(dataset_dict, DS_NORMATIVE)
            if value:
                self._add_resource_list_triple(
                    dataset_ref, DCT.conformsTo, value)

            # License (dataset license)
            if dataset_dict.get(DS_LICENSE):
                g.add((dataset_ref, DCT.license, URIRef(
                        dataset_dict.get(DS_LICENSE))))

            # Distributions/Resources
            for resource_dict in dataset_dict.get('resources', []):
                uri_resource = '%s/resource/%s' % (
                    dataset_ref, resource_dict['id'])
                distribution = URIRef(uri_resource)
                g.add((dataset_ref, DCAT.distribution, distribution))
                g.add((distribution, RDF.type, DCAT.Distribution))

                # Identifier
                self._add_triple_from_dict(
                    resource_dict, distribution, DCT.identifier, DS_RESOURCE_IDENTIFIER, None, False, False)

                # Title
                self._add_translated_triple_field_from_dict(
                    resource_dict, distribution, DCT.title, DS_RESOURCE_NAME_TRANSLATED, None)

                # License (dataset license)
                if dataset_dict.get(DS_LICENSE):
                    g.add((distribution, DCT.license, URIRef(
                        dataset_dict.get(DS_LICENSE))))

                # Access URL
                if resource_dict.get(DS_RESOURCE_ACCESS_URL):
                    g.add((distribution, DCAT.accessURL, Literal(
                        resource_dict.get(DS_RESOURCE_ACCESS_URL), datatype=XSD.anyURI)))

                # Format
                if resource_dict.get(DS_RESOURCE_FORMAT, None):
                    imt = URIRef("%s/format" % uri_resource)
                    g.add((imt, RDF.type, DCT.IMT))
                    g.add((distribution, DCT['format'], imt))

                    format = resource_dict.get(
                        DS_RESOURCE_FORMAT, None)
                    formats = dataset_dict.get(
                        EXPORT_AVAILABLE_RESOURCE_FORMATS, {})
                    label = None
                    if format and format in formats:
                        label = formats.get(format, None)
                    else:
                        _dataset = sh.scheming_get_schema(
                            'dataset', 'dataset')
                        res_format = sh.scheming_field_by_name(_dataset.get('resource_fields'),
                                                               'format')
                        formats[format] = sh.scheming_choices_label(
                            res_format['choices'], format)
                        label = formats.get(format, None)
                        dataset_dict[EXPORT_AVAILABLE_RESOURCE_FORMATS] = formats
                    if label:
                        g.add((imt, RDFS.label, Literal(label)))
                    g.add((imt, RDF.value, Literal(
                        resource_dict[DS_RESOURCE_FORMAT])))

                # Size
                if resource_dict.get(DS_RESOURCE_BYTE_SIZE):
                    try:
                        g.add((distribution, DCAT.byteSize,
                               Literal(float(resource_dict[DS_RESOURCE_BYTE_SIZE]),
                                       datatype=XSD.decimal)))
                    except (ValueError, TypeError):
                        g.add((distribution, DCAT.byteSize,
                               Literal(resource_dict[DS_RESOURCE_BYTE_SIZE])))
                # Relation
                value = self._get_dict_value(
                    dataset_dict, DS_NORMATIVE)
                if value:
                    self._add_resource_list_triple(
                        distribution, DCT.relation, value)

        except Exception, e:
            log.error("%s [dataset_ref: %s]. Unexpected Error %s: %s" % (
                method_log_prefix, dataset_ref, type(e).__name__, e))
        except:
            log.error("%s [dataset_ref: %s]. Unexpected Generic Error" % (
                method_log_prefix, dataset_ref))
        #log.debug('%s End method dataset_ref: %s' % (method_log_prefix, dataset_ref))

class CscSchemaOrgProfile(RDFProfile):
    '''
    An RDF profile based on the schema.org Dataset

    More information and specification:

    http://schema.org/Dataset

    Mapping between schema.org Dataset and DCAT:

    https://www.w3.org/wiki/WebSchemas/Datasets
    '''
    def graph_from_dataset(self, dataset_dict, dataset_ref):
        
        g = self.g

        # Namespaces
        self._bind_namespaces()

        g.add((dataset_ref, RDF.type, SCHEMA.Dataset))

        # Basic fields
        self._basic_fields_graph(dataset_ref, dataset_dict)

        # Catalog
        self._catalog_graph(dataset_ref, dataset_dict)

        # Groups
        self._groups_graph(dataset_ref, dataset_dict)

        # Tags
        self._tags_graph(dataset_ref, dataset_dict)

        #  Lists
        self._list_fields_graph(dataset_ref, dataset_dict)

        # Publisher
        self._publisher_graph(dataset_ref, dataset_dict)

        # Temporal
        self._temporal_graph(dataset_ref, dataset_dict)

        # Spatial
        self._spatial_graph(dataset_ref, dataset_dict)

        # Resources
        self._resources_graph(dataset_ref, dataset_dict)

        # Additional fields
        self.additional_fields(dataset_ref, dataset_dict)

    def additional_fields(self, dataset_ref, dataset_dict):
        '''
        Adds any additional fields.

        For a custom schema you should extend this class and
        implement this method.
        '''
        pass

    def _add_date_triple(self, subject, predicate, value, _type=Literal):
        '''
        Adds a new triple with a date object

        Dates are parsed using dateutil, and if the date obtained is correct,
        added to the graph as an SCHEMA.DateTime value.

        If there are parsing errors, the literal string value is added.
        '''
        if not value:
            return
        try:
            default_datetime = datetime.datetime(1, 1, 1, 0, 0, 0)
            _date = parse_date_util(value, default=default_datetime)

            self.g.add((subject, predicate, _type(_date.isoformat())))
        except ValueError:
            self.g.add((subject, predicate, _type(value)))

    def _bind_namespaces(self):
        self.g.bind('schema', namespaces['schema'])

    def _basic_fields_graph(self, dataset_ref, dataset_dict):
        items = [
            ('identifier', SCHEMA.identifier, None, Literal),
            ('title', SCHEMA.name, None, Literal),
            ('notes', SCHEMA.description, None, Literal),
            ('version', SCHEMA.version, ['dcat_version'], Literal),
            ('issued', SCHEMA.datePublished, ['metadata_created'], Literal),
            ('modified', SCHEMA.dateModified, ['metadata_modified'], Literal),
            ('license', SCHEMA.license, ['license_url', 'license_title'], Literal),
        ]
        self._add_triples_from_dict(dataset_dict, dataset_ref, items)

        items = [
            ('issued', SCHEMA.datePublished, ['metadata_created'], Literal),
            ('modified', SCHEMA.dateModified, ['metadata_modified'], Literal),
        ]

        self._add_date_triples_from_dict(dataset_dict, dataset_ref, items)

        # Dataset URL
        dataset_url = url_for('dataset_read',
                              id=dataset_dict['name'],
                              qualified=True)
        self.g.add((dataset_ref, SCHEMA.url, Literal(dataset_url)))

    def _catalog_graph(self, dataset_ref, dataset_dict):
        data_catalog = BNode()
        self.g.add((dataset_ref, SCHEMA.includedInDataCatalog, data_catalog))
        self.g.add((data_catalog, RDF.type, SCHEMA.DataCatalog))
        self.g.add((data_catalog, SCHEMA.name, Literal(config.get('ckan.site_title'))))
        self.g.add((data_catalog, SCHEMA.description, Literal(config.get('ckan.site_description'))))
        self.g.add((data_catalog, SCHEMA.url, Literal(config.get('ckan.site_url'))))

    def _groups_graph(self, dataset_ref, dataset_dict):
        for group in dataset_dict.get('groups', []):
            group_url = url_for(controller='group',
                                action='read',
                                id=group.get('id'),
                                qualified=True)
            about = BNode()

            self.g.add((about, RDF.type, SCHEMA.Thing))

            self.g.add((about, SCHEMA.name, Literal(group['name'])))
            self.g.add((about, SCHEMA.url, Literal(group_url)))

            self.g.add((dataset_ref, SCHEMA.about, about))

    def _tags_graph(self, dataset_ref, dataset_dict):
        for tag in dataset_dict.get('tagsssss', []):
            self.g.add((dataset_ref, SCHEMA.keywords, Literal(tag['name'])))

    def _list_fields_graph(self, dataset_ref, dataset_dict):
        items = [
            ('language', SCHEMA.inLanguage, None, Literal),
        ]
        self._add_list_triples_from_dict(dataset_dict, dataset_ref, items)

    def _publisher_graph(self, dataset_ref, dataset_dict):
        if any([
            self._get_dataset_value(dataset_dict, 'publisher_uri'),
            self._get_dataset_value(dataset_dict, 'publisher_name'),
            dataset_dict.get('organization'),
        ]):

            publisher_uri = publisher_uri_from_dataset_dict(dataset_dict)
            if publisher_uri:
                publisher_details = URIRef(publisher_uri)
            else:
                # No organization nor publisher_uri
                publisher_details = BNode()

            self.g.add((publisher_details, RDF.type, SCHEMA.Organization))
            self.g.add((dataset_ref, SCHEMA.publisher, publisher_details))


            publisher_name = self._get_dataset_value(dataset_dict, 'publisher_name')
            if not publisher_name and dataset_dict.get('organization'):
                publisher_name = dataset_dict['organization']['title']
            self.g.add((publisher_details, SCHEMA.name, Literal(publisher_name)))

            contact_point = BNode()
            self.g.add((contact_point, RDF.type, SCHEMA.ContactPoint))
            self.g.add((publisher_details, SCHEMA.contactPoint, contact_point))

            self.g.add((contact_point, SCHEMA.contactType, Literal('customer service')))

            publisher_url = self._get_dataset_value(dataset_dict, 'publisher_url')
            if not publisher_url and dataset_dict.get('organization'):
                publisher_url = dataset_dict['organization'].get('url') or config.get('ckan.site_url')

            self.g.add((contact_point, SCHEMA.url, Literal(publisher_url)))
            items = [
                ('publisher_email', SCHEMA.email, ['contact_email', 'maintainer_email', 'author_email'], Literal),
                ('publisher_name', SCHEMA.name, ['contact_name', 'maintainer', 'author'], Literal),
            ]

            self._add_triples_from_dict(dataset_dict, contact_point, items)

    def _temporal_graph(self, dataset_ref, dataset_dict):
        start = self._get_dataset_value(dataset_dict, 'temporal_start')
        end = self._get_dataset_value(dataset_dict, 'temporal_end')
        if start or end:
            if start and end:
                self.g.add((dataset_ref, SCHEMA.temporalCoverage, Literal('%s/%s' % (start, end))))
            elif start:
                self._add_date_triple(dataset_ref, SCHEMA.temporalCoverage, start)
            elif end:
                self._add_date_triple(dataset_ref, SCHEMA.temporalCoverage, end)

    def _spatial_graph(self, dataset_ref, dataset_dict):
        spatial_uri = self._get_dataset_value(dataset_dict, 'spatial_uri')
        spatial_text = self._get_dataset_value(dataset_dict, 'spatial_text')
        spatial_geom = self._get_dataset_value(dataset_dict, 'spatial')

        if spatial_uri or spatial_text or spatial_geom:
            if spatial_uri:
                spatial_ref = URIRef(spatial_uri)
            else:
                spatial_ref = BNode()

            self.g.add((spatial_ref, RDF.type, SCHEMA.Place))
            self.g.add((dataset_ref, SCHEMA.spatialCoverage, spatial_ref))

            if spatial_text:
                self.g.add((spatial_ref, SCHEMA.description, Literal(spatial_text)))

            if spatial_geom:
                geo_shape = BNode()
                self.g.add((geo_shape, RDF.type, SCHEMA.GeoShape))
                self.g.add((spatial_ref, SCHEMA.geo, geo_shape))

                # the spatial_geom typically contains GeoJSON
                self.g.add((geo_shape,
                       SCHEMA.polygon,
                       Literal(spatial_geom)))

    def _resources_graph(self, dataset_ref, dataset_dict):
        g = self.g
        for resource_dict in dataset_dict.get('resources', []):
            distribution = URIRef(resource_uri(resource_dict))
            g.add((dataset_ref, SCHEMA.distribution, distribution))
            g.add((distribution, RDF.type, SCHEMA.DataDownload))

            self._distribution_graph(distribution, resource_dict)

    def _distribution_graph(self, distribution, resource_dict):
        #  Simple values
        self._distribution_basic_fields_graph(distribution, resource_dict)

        # Lists
        self._distribution_list_fields_graph(distribution, resource_dict)

        # Format
        self._distribution_format_graph(distribution, resource_dict)

        # URL
        self._distribution_url_graph(distribution, resource_dict)

        # Numbers
        self._distribution_numbers_graph(distribution, resource_dict)

    def _distribution_basic_fields_graph(self, distribution, resource_dict):
        items = [
            ('name', SCHEMA.name, None, Literal),
            ('description', SCHEMA.description, None, Literal),
            ('license', SCHEMA.license, ['rights'], Literal),
        ]

        self._add_triples_from_dict(resource_dict, distribution, items)

        items = [
            ('issued', SCHEMA.datePublished, None, Literal),
            ('modified', SCHEMA.dateModified, None, Literal),
        ]

        self._add_date_triples_from_dict(resource_dict, distribution, items)

    def _distribution_list_fields_graph(self, distribution, resource_dict):
        items = [
            ('language', SCHEMA.inLanguage, None, Literal),
        ]
        self._add_list_triples_from_dict(resource_dict, distribution, items)

    def _distribution_format_graph(self, distribution, resource_dict):
        if resource_dict.get('format'):
            self.g.add((distribution, SCHEMA.encodingFormat,
                   Literal(resource_dict['format'])))
        elif resource_dict.get('mimetype'):
            self.g.add((distribution, SCHEMA.encodingFormat,
                   Literal(resource_dict['mimetype'])))

    def _distribution_url_graph(self, distribution, resource_dict):
        url = resource_dict.get('url')
        download_url = resource_dict.get('download_url')
        if download_url:
            self.g.add((distribution, SCHEMA.contentUrl, Literal(download_url)))
        if (url and not download_url) or (url and url != download_url):
            self.g.add((distribution, SCHEMA.url, Literal(url)))

    def _distribution_numbers_graph(self, distribution, resource_dict):
        if resource_dict.get('size'):
            self.g.add((distribution, SCHEMA.contentSize, Literal(resource_dict['size'])))
