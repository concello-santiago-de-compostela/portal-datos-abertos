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
 
import ckan.lib.helpers as h
import ckan.lib.munge as munge
import re
import json
import ckanext.csc_scheming.helpers as ch
import ckanext.fluent.helpers as fh
import geojson
from ckan.lib.i18n import get_available_locales

from ckan.plugins.toolkit import missing, get_validator, config, _

import logging
log = logging.getLogger(__name__)

DEFAULT_TITLE_FIELD = 'title_translated'
ISO_639_LANGUAGE = u'^[a-z][a-z][a-z]?[a-z]?$'
FREQUENCY_VALUES = [ "days", "weeks", "months", "years", "hours", "minutes", "seconds" ]

not_empty = get_validator('not_empty')

def scheming_validator(fn):
    """
    Decorate a validator for using with scheming.
    """
    fn.is_a_scheming_validator = True
    return fn

"""
FIELD URL FROM MULTILANGUAGE TITLE
"""
@scheming_validator
def csc_multilanguage_url(field, schema):

    def validator(key, data, errors, context):
        if errors[key]:
            return

        value = data[key]
        if value is not missing:
            if value:
                return

        output = {}

        prefix = field['autogeneration_field']
        if not prefix:
            prefix = DEFAULT_TITLE_FIELD

        log.debug('[csc_multilanguage_url] Creating field using the field %s', prefix)

        prefix = prefix + '-'

        extras = data.get(key[:-1] + ('__extras',), {})

        locales = []

        autogeneration_locale = field['autogeneration_locale']
        if autogeneration_locale:
            locales.append(autogeneration_locale)
        locale_default = config.get('ckan.locale_default', 'es')
        if locale_default:
            locales.append(locale_default)

        for l in locales:
            title_lang = prefix + l
            if title_lang in extras and extras[title_lang]:
                dataset_title = extras[title_lang]
                data[key] = munge.munge_title_to_name(dataset_title)
                log.debug('[csc_multilanguage_url] Created name "%s" for package from language %s',
                            data[key], l)
                break
        return

    return validator

"""
FIELD TYPE URL
"""
@scheming_validator
def csc_uri_text(field, schema):
    def validator(key, data, errors, context):
        value = data[key]

        is_url = False
        if ('is_url' in field):
            is_url = field['is_url']

        if value is not missing:
            if value:
                if is_url and not h.is_url(value):
                    errors[key].append(_('the URL format is not valid'))
                else:
                    if not is_url and not ch.csc_is_uri(value):
                        errors[key].append(_('the URI format is not valid'))
                return

        # 3. separate fields
        extras = data.get(('__extras',), {})
        if key in extras:
            value = extras[key]

            if is_url and not h.is_url(value):
                errors[key].append(_('the URL format is not valid'))
            else:
                if not is_url and not ch.csc_is_uri(value):
                    errors[key].append(_('the URI format is not valid'))
            return

        if field.get('required'):
            not_empty(key, data, errors, context)

    return validator

def csc_uri_text_output(value):
    return value


"""
FIELD TYPE DATE FREQUENCY
"""
@scheming_validator
def csc_date_frequency(field, schema):
    def validator(key, data, errors, context):
        """
        JSON with frequency and value information
        """
        # just in case there was an error before that validator
        if errors[key]:
            return

        value = data[key]

        # 1. list of strings or 2. single string
        if value is not missing:
            if isinstance(value, basestring):
                try:
                    value = json.loads(value)
                except UnicodeDecodeError:
                    errors[key].append(_('Invalid encoding for JSON string'))
                    return
                except ValueError:
                    errors[key].append(_('Failed to decode JSON string'))
                    return
            if not isinstance(value, dict):
                errors[key].append(_('Expecting JSON object'))
                return

            if not 'type' in value or not 'value' in value:
                errors[key].append(_('The JSON object must contain type and value keys'))
                return

            frequency_type = value['type']
            frequency_value = value['value']

            if frequency_type and frequency_value:
                if not frequency_type in FREQUENCY_VALUES:
                    errors[key] = [_('The frequency type is no allowed')]
                try:
                   int(frequency_value)
                except ValueError:
                    errors[key] = [_('The frequency value is not an integer')]
            else:
                if frequency_type and not frequency_value:
                    errors[key] = [_('The frequency value is mandatory')]
                if frequency_value and not frequency_type:
                    errors[key] = [_('The frequency type is mandatory')]
                if field.get('required') and not frequency_value and not frequency_type:
                    not_empty(key, data, errors, context)

            if not errors[key]:
                if frequency_value and frequency_type:
                    out = { 'type': frequency_type, 'value': frequency_value}
                    data[key] = json.dumps(out)
                else:
                    data[key] = None
            return

        # 3. separate fields
        found = {}
        prefix = key[-1] + '-'
        extras = data.get(key[:-1] + ('__extras',), {})

        #Form validations
        frequency_type = extras.get(prefix+ 'type')
        frequency_value = extras.get(prefix + 'value')

        if frequency_type and frequency_value:
            if not frequency_type in FREQUENCY_VALUES:
                errors[key] = [_('The frequency type is no allowed')]
            try:
               int(frequency_value)
            except ValueError:
                errors[key] = [_('The frequency value is not an integer')]
        else:
            if frequency_type and not frequency_value:
                errors[key] = [_('The frequency value is mandatory')]
            if frequency_value and not frequency_type:
                errors[key] = [_('The frequency type is mandatory')]
            if field.get('required') and not frequency_value and not frequency_type:
                not_empty(key, data, errors, context)

        #With errors we finish
        if errors[key]:
            return

        #transform to JSON
        if frequency_value and frequency_type:
            out = { 'type': frequency_type, 'value': frequency_value}
            data[key] = json.dumps(out)
        else:
            data[key] = None

    return validator


def csc_date_frequency_output(value):
    """
    Return stored json representation as a dict, if
    value is already a dict just pass it through.
    """
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    try:
        return json.loads(value)
    except ValueError:
        return {}

"""
FIELD TYPE DATE PERIOD
"""
@scheming_validator
def csc_date_period(field, schema):
    def validator(key, data, errors, context):
        """
        1. a JSON with dates, eg.
           {"1": {"to": "2016-05-28T00:00:00", "from": "2016-05-11T00:00:00"}}
        2. separate fields per date and time (for form submissions):
           fieldname-to-date-1 = "2012-09-11"
           fieldname-to-time-1 = "11:00"
           fieldname-from-date-2 = "2014-03-03"
           fieldname-from-time-2 = "09:45"
        """
        # just in case there was an error before that validator
        if errors[key]:
            return

        value = data[key]

        # 1. json
        if value is not missing:
            if isinstance(value, basestring):
                try:
                    value = json.loads(value)
                except ValueError, e:
                    errors[key].append(_('Invalid field structure, it is not a valid JSON'))
                    return
                if not isinstance(value, dict):
                 errors[key].append(_('Expecting valid JSON value'))
                 return

            out = {}
            for element in sorted(value):
                dates = value.get(element)
                with_date = False
                #if dates['from']:
                if 'from' in dates:
                    try:
                        date = h.date_str_to_datetime(dates['from'])
                        with_date = True
                    except (TypeError, ValueError), e:
                        errors[key].append(_('From value: Date format incorrect'))
                        continue
                #if dates['to']:
                if 'to' in dates:
                    try:
                        date = h.date_str_to_datetime(dates['to'])
                        with_date = True
                    except (TypeError, ValueError), e:
                        errors[key].append(_('To value: Date format incorrect'))
                        continue

                if not with_date:
                    errors[key]. append(_('Date period without from and to'))
                    continue
                out[str(element)] = dates

            if not errors[key]:
                data[key] = json.dumps(out)
            return

        # 3. separate fields
        found = {}
        short_prefix = key[-1] + '-'
        prefix = key[-1] + '-date-'
        extras = data.get(key[:-1] + ('__extras',), {})

        #Fase de validacion
        datetime_errors = False
        valid_indexes = []
        for name, text in extras.iteritems():
            if not name.startswith(prefix):
                continue
            if not text:
                continue

            datetime = text
            #Get time if exists
            index = name.split('-')[-1]
            type_field = name.split('-')[-2]
            time_value = extras.get(short_prefix+'time-'+type_field+'-'+index)
            #Add the time
            if time_value:
                datetime = text + ' ' + time_value

            #Create datetime and validation
            try:
                date = h.date_str_to_datetime(datetime)
                valid_indexes.append(index)
            except (TypeError, ValueError), e:
                errors[key].append(_('Date time format incorrect'))
                datetime_errors = True

        if datetime_errors:
            return

        valid_indexes = sorted(list(set(valid_indexes)))
        new_index = 1
        for index in valid_indexes:
            period = {}

            #Get from
            date_from_value = extras.get(short_prefix+'date-from-'+index)
            if date_from_value:
                datetime = date_from_value
                time_from_value = extras.get(short_prefix+'time-from-'+index)
                if time_from_value:
                    datetime = date_from_value + " " + time_from_value
                try:
                    date = h.date_str_to_datetime(datetime)
                    period['from'] = date.strftime("%Y-%m-%dT%H:%M:%S")
                except (TypeError, ValueError), e:
                    continue

            date_to_value = extras.get(short_prefix+'date-to-'+index)
            if date_to_value:
                datetime = date_to_value
                time_to_value = extras.get(short_prefix+'time-to-'+index)
                if time_to_value:
                    datetime = date_to_value + " " + time_to_value
                try:
                    date = h.date_str_to_datetime(datetime)
                    period['to'] = date.strftime("%Y-%m-%dT%H:%M:%S")
                except (TypeError, ValueError), e:
                    continue

            if period:
                found[new_index] = period
                # only adds 1 to the new index with good periods
                new_index = new_index+1

        out = {}
        for i in sorted(found):
            out[i] = found[i]
        data[key] = json.dumps(out)

    return validator


def csc_date_period_output(value):
    """
    Return stored json representation as a dict, if
    value is already a dict just pass it through.
    """
    if isinstance(value, dict):
        return value
    if value is None or isinstance(value, list):
        return {}
    try:
        return json.loads(value)
    except ValueError:
        return {}


"""
FIELD TYPE MULTIPLE URL
"""
@scheming_validator
def csc_multiple_uri_text(field, schema):
    def validator(key, data, errors, context):
        """
        Accept repeating text input in the following forms
        and convert to a json list for storage:
        1. a list of strings, eg.
           ["http://url1", "http://url2"]
        2. a single string value to allow single text fields to be
           migrated to repeating text
           "http://url1"
        3. separate fields per language (for form submissions):
           fieldname-0 = "http://url1"
           fieldname-1 = "http://url2"
        """
        # just in case there was an error before that validator
        if errors[key]:
            return

        value = data[key]

        is_url = False
        if ('is_url' in field):
            is_url = field['is_url']

        # 1. list of strings or 2. single string
        if value is not missing:
            if isinstance(value, basestring):
                value = [value]
            if not isinstance(value, list):
                errors[key].append(_('Expecting list of strings'))
                return

            out = []
            for element in value:
                if not isinstance(element, basestring):
                    errors[key].append(_('Invalid type for repeating url text: {el}').format(el=element))
                    continue
                try:
                    if not isinstance(element, unicode):
                        element = element.decode('utf-8')
                    if element:
                        if is_url and not h.is_url(element):
                            errors[key].append(_('The URL format is not valid'))
                        else:
                            if not is_url and not ch.csc_is_uri(element):
                                errors[key].append(_('The URI format is not valid'))

                except UnicodeDecodeError:
                    errors[key]. append(_('Invalid encoding for "{l}" value'.format(l=lang)))
                    continue
                out.append(element)

            if not errors[key]:
                data[key] = json.dumps(out)
            return

        # 3. separate fields
        found = {}
        prefix = key[-1] + '-'
        extras = data.get(key[:-1] + ('__extras',), {})

        #Validation
        url_errors = False
        for name, text in extras.iteritems():
            if not name.startswith(prefix):
                continue
            if not text:
                continue
            index = name.split('-', 1)[1]
            if text is not missing:
                if is_url and not h.is_url(text):
                    url_errors = True
                    name_error = key[:-1] + (name,)
                    errors[name_error] = [_('The URL format for "{t}" is not valid').format(t=text)]
                else:
                    if not is_url and not ch.csc_is_uri(text):
                        url_errors = True
                        name_error = key[:-1] + (name,)
                        errors[name_error] = [_('The URI format for "{t}" is not valid').format(t=text)]

        if url_errors:
            return

        for name, text in extras.iteritems():
            if not name.startswith(prefix):
                continue
            if not text:
                continue
            index = name.split('-', 1)[1]
            try:
                index = int(index)
            except ValueError:
                continue
            found[index] = text

        out = [found[i] for i in sorted(found)]
        data[key] = json.dumps(out)

    return validator

def csc_multiple_uri_text_output(value):
    """
    Return stored json representation as a list, if
    value is already a list just pass it through.
    """
    if isinstance(value, list):
        return value
    if value is None:
        return []
    try:
        return json.loads(value)
    except ValueError:
        return [value]

@scheming_validator
def csc_fluent_text(field, schema):
    """
    Accept multilingual text input in the following forms
    and convert to a json string for storage:

    1. a multilingual dict, eg.

       {"en": "Text", "fr": "texte"}

    2. a JSON encoded version of a multilingual dict, for
       compatibility with old ways of loading data, eg.

       '{"en": "Text", "fr": "texte"}'

    3. separate fields per language (for form submissions):

       fieldname-en = "Text"
       fieldname-fr = "texte"

    When using this validator in a ckanext-scheming schema setting
    "required" to true will make all form languages required to
    pass validation.
    """
    # combining scheming required checks and fluent field processing
    # into a single validator makes this validator more complicated,
    # but should be easier for fluent users and eliminates quite a
    # bit of duplication in handling the different types of input
    required_langs = []

    if field and field.get('required'):
        required_langs = fh.fluent_form_languages(field, schema=schema)

    def validator(key, data, errors, context):
        # just in case there was an error before our validator,
        # bail out here because our errors won't be useful
        if errors[key]:
            return

        value = data[key]
        # 1 or 2. dict or JSON encoded string
        if value is not missing:
            if isinstance(value, basestring):
                try:
                    value = json.loads(value)
                except UnicodeDecodeError:
                    errors[key].append(_('Invalid encoding for JSON string'))
                    return
                except ValueError:
                    errors[key].append(_('Failed to decode JSON string'))
                    return
            if not isinstance(value, dict):
                errors[key].append(_('expecting JSON object'))
                return

            for lang, text in value.iteritems():
                if text and not text.isspace():
                    try:
                        m = re.match(ISO_639_LANGUAGE, lang)
                    except TypeError:
                        errors[key].append(_('invalid type for language code: {l}').format(l=lang))
                        continue
                    if not m:
                        errors[key].append(_('invalid language code: "{l}"').format(l=lang))
                        continue
                    if not isinstance(text, basestring):
                        errors[key].append(_('invalid type for "{l}" value').format(l=lang))
                        continue
                    if isinstance(text, str):
                        try:
                            value[lang] = text.strip().decode('utf-8')
                        except UnicodeDecodeError:
                            errors[key]. append(_('invalid encoding for "{l}" value').format(l=lang))

            for lang in required_langs:
                if not value.get(lang):
                    errors[key].append(_('Required language "{l}" missing').format(l=lang))

            if not errors[key]:
                data[key] = json.dumps(value)
            return

        # 3. separate fields
        output = {}
        prefix = key[-1] + '-'
        extras = data.get(key[:-1] + ('__extras',), {})

        for name, text in extras.iteritems():
            if not name.startswith(prefix):
                continue
            lang = name.split('-', 1)[1]
            m = re.match(ISO_639_LANGUAGE, lang)
            if not m:
                errors[name] = [_('invalid language code: "{l}"').format(l=lang)]
                output = None
                continue

            if text and not text.isspace():
                if output is not None:
                    output[lang] = text.strip()

        for lang in required_langs:
            if not extras.get(prefix + lang) or extras.get(prefix + lang).isspace():
                errors[key[:-1] + (key[-1] + '-' + lang,)] = [_('Missing value')]
            output = None

        if output is None:
            return

        for lang in output:
            del extras[prefix + lang]
        data[key] = json.dumps(output)

    return validator


def csc_fluent_text_output(value):
    """
    Return stored json representation as a multilingual dict, if
    value is already a dict just pass it through.
    """
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except ValueError:
        # plain string in the db, assume default locale
        return {config.get('ckan.locale_default', 'en'): value}

"""
FIELD TYPE SPATIAL
"""
@scheming_validator
def csc_spatial(field, schema):
    def validator(key, data, errors, context):
        """
        1. a JSON with dates, eg.
            {"type": "Point", "coordinates": [100.0, 0.0]}
            {
             "type": "Polygon", 
             "coordinates": [[[100.0,0.0],[101.0,0.0],[101.0,1.0],[100.0,1.0], [100.0,0.0]]]
            }
     
        2. separate fields per point  (for form submissions):
           fieldname-spatial_coord1 = "100.0,0.0"
           fieldname-spatial_coord2 = "101.0,0.0"
           fieldname-spatial_coord3 = "101.0,1.0"
           fieldname-spatial_coord4 = "100.0,1.0"
        """
        # just in case there was an error before that validator
        if errors[key]:
            return

        value = data[key]
        
        # 1. json
        if value and value is not missing:
            if isinstance(value, basestring):
                try:
                    value = json.loads(value)
                except ValueError, e:
                    errors[key].append(_('Invalid field structure, it is not a valid JSON'))
                    return
            if not isinstance(value, dict):
                 errors[key].append(_('Expecting valid JSON value'))
                 return

            coordType = value['type']
            coordinates = value['coordinates']
            out = {}
            out['type'] = coordType
            if not(coordType == 'Point'or coordType == 'Polygon'):
                errors[key].append(_('Invalid spatial type'))
                return

            if (coordType == 'Point'):
                if coordinates and len(coordinates) != 2:
                    errors[key].append(_('It is not a valid Point'))
                    return
                if (geojson.Point(coordinates).is_valid == False):
                    errors[key].append(_('It is not a valid Point'))
                    return
                
                out['coordinates'] = coordinates
            
            elif coordType == 'Polygon':
                if len(coordinates[0]) < 3 or len(coordinates[0]) > 5:
                    errors[key].append(_('It is not a valid spatial Polygon'))
                    return
                coord_tuples = []
                for coord in coordinates[0]:
                    coord_tuples.append(tuple(coord))
                coord_tuples = [coord_tuples]
                poly = geojson.Polygon(coord_tuples)
                if (poly.is_valid == False):
                    log.info("[csc_spatial] Error " + poly.errors())
                    errors[key].append(_('It is not a valid Polygon'))
                    return
                out['coordinates'] = coord_tuples
            
           
            if not errors[key]:
                data[key] = json.dumps(out, sort_keys=True)

            return

        # 3. separate fields
        short_prefix = key[-1] + '-'
        prefix = key[-1] + '-coord-'
        extras = data.get(key[:-1] + ('__extras',), {})

        #Fase de validacion

        valid_indexes = []
        valid_points = {}
        patron = re.compile(r'^(\-?\d+(\.\d+)?),\s*(\-?\d+(\.\d+)?)$') #patrón que debe cumplir

        for name, text in extras.iteritems():
            if not name.startswith(prefix):
                continue
            if not text:
                continue
         
            #Get coordinate if exists
            index = name.split('-')[-1]
            coor_value = extras.get(short_prefix+'coord-'+index)
            key_coord = _( 'Coordinate ') + index + ": "
            lat = None
            lon = None
            #Create point and validation
            try:
                if not patron.match(coor_value):
                    errors[key].append(key_coord + _('Wrong point {p}'.format(p=coor_value)))
                else:
                    if (coor_value):
                        split_coor_value = coor_value.split(',')
                        lat = float(split_coor_value[0].strip())
                        lon = float(split_coor_value[1].strip())
                        t = (lat, lon)
                        if (lat < float(-90.0) or lat > float(90.0)):
                            log.info('[csc_spatial] Wrong latitude {l}'.format(l=lat))
                            errors[key].append(key_coord + _('Wrong latitude {l}'.format(l=lat)))
                        if (lon < -180.0 or lon > 180.0):
                            log.info('[csc_spatial] Wrong longitude {l}'.format(l=lon))
                            errors[key].append(key_coord + _('Wrong longitude {l}'.format(l=lon)))
                    
                        point = geojson.Point(t)
                        log.info('[csc_spatial] point %s', point)
                        if point.is_valid:
                            valid_indexes.append(index)
                            valid_points[index] = t
                        else:
                            log.info('[csc_spatial] point.errors %s', point.errors())
                            errors[key].append(key_coord + point.errors())
            except (TypeError, ValueError), e:
                log.info('[csc_spatial] {l}'.format(l=e))
                errors[key].append(key_coord + _('Point incorrect'))

        if errors[key] and len(errors[key]) > 0:
            for error in errors[key]:
                log.info('[csc_spatial] error {l}'.format(l=error))
            

        out = {}
        valid_indexes_len = len(valid_indexes)
        if field and field.get('required') and valid_indexes_len == 0:
            errors[key].append(_( 'required'))
        if valid_indexes_len == 1 or valid_indexes_len == 3 or valid_indexes_len == 4:
            if valid_indexes_len == 1:
                poly = geojson.Point(valid_points[valid_indexes[0]])
                log.info("[csc_spatial] Point created")
            else:
                points = []
                valid_indexes.sort()
                for i in valid_indexes:
                    points.append(valid_points[i])

                points.append(points[0])
                poly = geojson.Polygon([points])
                log.info("Polygon created {l}".format(l=poly))
            out = poly
            if poly.is_valid == False:
                log.info("[csc_spatial] Error " + poly.errors())
                errors[key].append(_('Wrong coordinates'))                   
            else:
                log.info("[csc_spatial] coordinates number = {l}".format(l=valid_indexes_len))
                if field and field.get('required'):
                    errors[key].append(_('Expecting one, three or four coordinates')) 

    
        data[key] = json.dumps(out)

    return validator


def csc_spatial_output(value):
    """
    Return stored json representation as a dict, if
    value is already a dict just pass it through.
    """
    if isinstance(value, dict):
        return value
    if value is None or isinstance(value, list):
        return {}
    try:
        return json.loads(value)
    except ValueError:
        return {}
