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
 
from ckanext.scheming.helpers import lang
from ckan.plugins.toolkit import config, _, ungettext

import re

import logging
log = logging.getLogger(__name__)

def csc_scheming_language_text(text, prefer_lang=None):
    """
    :param text: {lang: text} dict or text string
    :param prefer_lang: choose this language version if available

    Convert "language-text" to users' language by looking up
    languag in dict or using gettext if not a dict
    """
    log.debug('[csc_scheming_language_text] text %s prefer_lang %s', text, prefer_lang)
    if not text:
        final_text = u''

    assert text != {}
    if hasattr(text, 'get'):
        try:
            if prefer_lang is None:
                prefer_lang = lang()
        except TypeError:
            prefer_lang = config.get('ckan.locale_default', 'es')
        else:
            try:
                final_text = text[prefer_lang]
            except KeyError:
                pass

        if not final_text:
            locale_order = config.get('ckan.locale_order', '').split()
            for l in locale_order:
                if l in text and text[l]:
                    final_text = text[l]
                    break
        log.debug('[csc_scheming_language_text] final_text %s', final_text)
        return final_text

    t = gettext(text)

    if isinstance(text, str):
        text = text.decode('utf-8')
    t = _(text)
    log.debug('[csc_scheming_language_text] t %s', t)
    return t



def csc_dataset_form_value(text):
    """
    :param text: {lang: text} dict or text string

    Convert "language-text" to users' language by looking up
    languag in dict or using gettext if not a dict but. If the text
    doesn't exist look for an available text
    """
    if not text:
        return u''

    if hasattr(text, 'get'):
        final_text = u''
        try:
            prefer_lang = lang()
        except:
            prefer_lang = config.get('ckan.locale_default', 'es')
        else:
            try:
                final_text = text[prefer_lang]
            except KeyError:
                pass

        if not final_text:
            locale_order = config.get('ckan.locale_order', '').split()
            for l in locale_order:
                if l in text and text[l]:
                    final_text = text[l]
                    break
        return final_text

    t = gettext(text)
    if isinstance(t, str):
        return t.decode('utf-8')
    return t

def csc_dataset_form_lang_and_value(text):
    """
    :param text: {lang: text} dict or text string

    Convert "language-text" to users' language by looking up
    languag in dict, if the text
    doesn't exit look for an available text
    """
    if not text:
        return {'': u''}

    if hasattr(text, 'get'):
        final_text = u''
        try:
            prefer_lang = lang()
        except:
            prefer_lang = config.get('ckan.locale_default', 'es')
        else:
            try:
                prefer_lang = str(prefer_lang)
                final_text = text[prefer_lang]
            except KeyError:
                pass

        if not final_text:
            locale_order = config.get('ckan.locale_order', '').split()
            for l in locale_order:
                if l in text and text[l]:
                    final_text = text[l]
                    prefer_lang = l
                    break

        return {prefer_lang: final_text}

    return {'': u''}

def csc_is_uri(value):
    '''
    Given a value, raises an RDFParsesException if value is not a complete
    URI.
    A complete URI starts with scheme_name: ([A-Za-z][A-Za-z0-9+.-]*):
    '''
    is_uri = False
    pattern = '^([A-Za-z][A-Za-z0-9+.-]*):'
    if (value and value.strip() != '' and re.match(pattern, value)):
        is_uri = True

    return is_uri


def csc_multiple_field_required(field, lang):
    """
    Return field['required'] or guess based on validators if not present.
    """
    if 'required' in field:
        return field['required']
    if 'required_language' in field and field['required_language'] == lang:
        return True
    return 'not_empty' in field.get('validators', '').split()


