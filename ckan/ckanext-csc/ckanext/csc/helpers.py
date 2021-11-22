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
 
import urllib
import json
import logging
import json
import datetime
import pytz
import calendar

from ckanext.scheming import helpers as sh
from ckanext.csc_scheming import helpers as csh
from ckanext.scheming.helpers import lang
from ckan.plugins.toolkit import c, config, _, ungettext, request, h, asbool
from operator import itemgetter
from time import strptime

log = logging.getLogger(__name__)

def csc_default_locale():
    '''
    Returns default locale
    '''
    return config.get('ckan.locale_default', 'es').lower()



def csc_exported_catalog_files():
    '''
    Returns endpoint of download catalog files in rdf, csv and atom format
    '''
    url_rdf = config.get('ckanext.csc.catalog.export.rdf.url', '#')
    return url_rdf



def csc_theme_id(theme=None):
    '''
    Given a value of theme, returs its identifier
    :param theme: value theme 
    :type string 
    
    :rtype string
    '''
    id = None
    if theme:
        index = theme.rfind('/')
        if (index > -1 and (index+1 < len(theme))):
            id = theme[index+1:]
    return id

def csc_list_themes(themes=None):
    '''
    Given an theme list values, get theirs translated labels
    
    :param themes: value theme list
    :type string list
    
    :rtype (string, string) list
    '''
    dataset = sh.scheming_get_schema('dataset', 'dataset')
    formats = sh.scheming_field_by_name(dataset.get('dataset_fields'),
                'theme')
    label_list = []
    for theme in themes:
        label = sh.scheming_choices_label(formats['choices'], theme)
        if label:
            label_list.append((csc_theme_id(theme), label))
    return label_list

def csc_dataset_field_value(text):
    """
    :param text: {lang: text} dict or text string

    Convert "language-text" to users' language by looking up
    language in dict or using gettext if not a dict but. If the text
    doesn't exist look for an available text
    """
    value = None
    language = None
    if not text:
        result = u''

    dict_text = csh.csc_dataset_form_lang_and_value(text)
    if (dict_text):
        language = sh.lang()
        if (dict_text.has_key(language) and dict_text[language] and \
            dict_text[language].strip() != ''):
            value = dict_text[language]
            language = None
        else:
            for key in dict_text:
                if (dict_text[key] and dict_text[key].strip() != ''):
                    value = (dict_text[key])
                    language = key
                    break
    return language, value

def csc_dataset_display_frequency(value, stype):
    '''
    Given a value and type frequency, get the translated label
    
    :param value: value of frequency
    :type int
    
    :param stype: type of frequency
    :type string
    
    :rtype string (frequency label)
    '''
    result = None
    years = {'1':_('Annual'), '2':_('Biennial'), '3':_('Triennial')}
    months = {'1':_('Monthly'), '2':_('Bimonthly'), '3':_('Quarterly'), '4':_('Three times a year'), '6':_('Semiannual')}
    weeks = {'1':_('Weekly'), '2':_('Biweekly')}
    days = {'1':_('Daily'), '2':_('Three times a week'), '3':_('Semiweekly'), '7':_('Weekly'), '10':_('Three times a month'), '15':_('Semimonthly')}
    hours = {'12': _('Twice a day')}
    seconds = {'1': _('Continuous')}
    types = ['seconds', 'minutes', 'hours', 'days', 'weeks', 'months', 'years']
    # Para que sean detectados al exportar literales
    sing_translate_types = [_('second'), _('minute'), _('hour'), _('day'), _('week'), _('month'), _('year')]
    plural_translate_types = [_('seconds'), _('minutes'), _('hours'), _('days'), _('weeks'), _('months'), _('years')]
    upper_plural_translate_types = [_('Seconds'), _('Minutes'), _('Hours'), _('Days'), _('Weeks'), _('Months'), _('Years')]
    if value and stype and stype in types:      
        num = int(float(value))
        svalue = str(value)
        if stype == 'years':
            if svalue in years:
                result = years[svalue] 
            else:
               result = ungettext('Every {num} year', 'Every {num} years', num).format(num=value)
        elif stype == 'months':
            if svalue in months:
                result = months[svalue]
            else:
                result = ungettext('Every {num} month', 'Every {num} months', num).format(num=value) 
        elif stype == 'weeks':
            if svalue in weeks:
                result = weeks[svalue] 
            else:
                result = ungettext('Every {num} week', 'Every {num} weeks', num).format(num=value)
        elif stype == 'days':
            if svalue in days:
                result = days[svalue] 
            else:
               result = ungettext('Every {num} day', 'Every {num} days', num).format(num=value)
        elif stype == 'hours':
            if svalue in hours:
                result = hours[svalue]
            else:
                result = ungettext('Every {num} hour', 'Every {num} hours', num).format(num=value)
        elif stype == 'seconds':
            if svalue in seconds:
                result = seconds[svalue] 
            else:
                result = ungettext('Every {num} second', 'Every {num} seconds', num).format(num=value)
        if result is None:
            result = _('Every') + ((' %s %s') % (value, _(stype))) 
        return result



def csc_resource_display_name_or_desc(name=None, description=None):
    '''
    Given a resource name, returns resourcename, 
          else returns given resource description
    
    :param name: resource name
    :type string
    
    :param stype: resource description
    :type string
    
    :rtype string (resource display name)
    '''
    if name:
        return name
    elif description:
        description = description.split('.')[0]
        max_len = 60
        if len(description) > max_len:
            description = description[:max_len] + '...'
        return description
    else:
        return _("Unnamed resource")



def csc_render_datetime(datetime_, date_format=None, with_hours=False):
    '''Render a datetime object or timestamp string as a localised date or
    in the requested format.
    If timestamp is badly formatted, then a blank string is returned.

    :param datetime_: the date
    :type datetime_: datetime or ISO string format
    :param date_format: a date format
    :type date_format: string
    :param with_hours: should the `hours:mins` be shown
    :type with_hours: bool

    :rtype: string
    '''
    if not datetime_:
        return ''
    if isinstance(datetime_, basestring):
        try:
            datetime_ = h.date_str_to_datetime(datetime_)
        except TypeError:
            return None
        except ValueError:
            return None
    # check we are now a datetime
    if not isinstance(datetime_, datetime.datetime):
        return None

    #Timezone in csc is always Europe/Madrid
    from_timezone = pytz.timezone('Europe/Madrid')
    to_timezone = pytz.timezone('UTC')
    datetime_ = from_timezone.localize(datetime_)
    # if date_format was supplied we use it
    if date_format:
        return datetime_.strftime(date_format)

    # the localised date
    datetime_ = datetime_.astimezone(tz=to_timezone)

    details = {
        'min': datetime_.minute,
        'hour': datetime_.hour,
        'day': datetime_.day,
        'year': datetime_.year,
        'month': datetime_.month,
        'timezone': datetime_.tzinfo.zone,
    }
    if with_hours:
        result = ('{day}/{month:02}/{year} {hour:02}:{min:02} ({timezone})').format(**details)
    else:
        result = ('{day}/{month:02}/{year}').format(**details)
    return result

def csc_dataset_display_name(package_or_package_dict):
    """
    Get title and language of a package
    
    :param package_or_package_dict: the package
    :type dict or package: 
    
    :rtype string, string: translated title, and locale
    """
    if isinstance(package_or_package_dict, dict):
        language, value = csc_dataset_field_value(package_or_package_dict.get('title_translated'))
    else:
        language, value = csc_dataset_field_value(package_or_package_dict.title_translated)
    return value

def csc_resource_display_name(resource_or_resource_dict):
    """
    Get title and language of a resource
    
    :param resource_or_resource_dict: the resource
    :type dict or resource: 
    
    :rtype string, string: translated title, and locale
    """
    if isinstance(resource_or_resource_dict, dict):
        language, value = csc_dataset_field_value(resource_or_resource_dict.get('name_translated'))
    else:
        language, value = csc_dataset_field_value(resource_or_resource_dict.name_translated)
    if value:
        return value
    else:
        return _("Unnamed resource")

def csc_dataset_tag_list_display_names(tags=None):
    ''' get a list of tags display_name separated by commas
    :param keys: tags 
    :type keys: list

    :rtype: string with display_name of tags separated by commas
    '''
    result = ""
    if tags:
        for tag in tags:
            if tag and tag.get('display_name'):
                result = result + "," + tag.get('display_name')
    if result and len(result)>0:
        return result[1:]

def csc_get_portal_name():
    """
    Get portal name
    
    :rtype string: portal name
    """
    #TODO - establecer valor por defecto correccto
    return config.get('ckan.site_title', 'santiagodecompostela.gal')



def csc_dataset_display_fields(field_name_list, dataset_fields):
    """
    :param field_name_list: list of scheme field names
    :param dataset_fields:  fields of dataset

    Return a dictionary with field names in field_name_list and
    value field in scheme. None if field not exists in scheme
    """
    dataset_dict = {}
    if field_name_list:
        for field_name in field_name_list:
            dataset_dict[field_name] = None

        if dataset_fields:
            for field in dataset_fields:
                if field and field['field_name'] and field['field_name'] in field_name_list:
                    dataset_dict[field['field_name']] = field
    return dataset_dict


def csc_sort_alphabetically_resources(resources = None):
    if not resources:
        return
    new_resources = []
    for res in resources:
        language, value= csc_dataset_field_value(res.get('name_translated'))
        if not value:
            value = _("Unnamed resource")
        new_res = {'lang': language, 'value': value, 'resource': res}
        new_resources.append(new_res)
    sorted_resources = sorted(new_resources, key=itemgetter('value'), reverse=False)
    return sorted_resources


def csc_get_addthis_route():
    """
    Get the addthis javascript url 
    """
    return config.get('ckanext.csc.addthis', '//s7.addthis.com/js/300/addthis_widget.js')


def csc_list_reduce_resource_format_label(resources=None, field_name='format'):
    '''
    Given an resource list, get label of resource_format
    
    :param resources: resource dict
    :type dict list
    
    :param field_name: field_name of resource
    :type string
    
    :rtype string list
    '''
    
    format_list = h.dict_list_reduce(resources, field_name)
    dataset = sh.scheming_get_schema('dataset', 'dataset')
    formats = sh.scheming_field_by_name(dataset.get('resource_fields'),
                'format')
    label_list = []
    for res_format in format_list:
        res_format_label = sh.scheming_choices_label(formats['choices'], res_format)
        if res_format_label:
            label_list.append(res_format_label)
    return label_list

def csc_resource_format_label(res_format=None):
    '''
    Given an format, get its label
    
    :param res_format: format
    :type string
    
    :rtype string
    '''
    if format:
        dataset = sh.scheming_get_schema('dataset', 'dataset')
        formats = sh.scheming_field_by_name(dataset.get('resource_fields'),
                'format')
        res_format_label = sh.scheming_choices_label(formats['choices'], res_format)
        if res_format_label:
            return res_format_label
    return res_format

def csc_get_cookieconsent_link(lang=None):
    """
    Get the cookie consent link 
    """
    links = config.get('ckanext.csc.cookieconsent.link', None)
    if links:
        slinks = links.split(' ')
    if not lang:
        lang = config.get('ckan.locale_default', None)
    for slink in slinks:
        if slink.find(lang + ':') == 0:
            return slink[(len(lang)+1):]    
    return ''

def _csc_get_filepath(filename = None):
    url = None
    try:
        directory = config.get('ckanext.csc.storage.directory.path', None)
        if directory and filename:
            url = '%s%s' % (directory, filename)
    except:
        url = None
    return url


##################################################
## METODOS PARA OBTENCION DE MENU DEL PRINCIPAL ##
## Y MENU DEL PIE DESDE FICHEROS JSON           ##
##################################################
def csc_main_menu_items():
    '''
    Returns data for footer menu items 
    Get data of endpoint set in ckanext.csc.footer.menu.items config property
    '''
    data = None
    logo_item = None
    menu_items = None
    try:
        url = _csc_get_filepath(config.get('ckanext.csc.main.menu.items', None))
        if url:
            response = urllib.urlopen(url)
            if response:
                data = json.loads(response.read().decode('utf-8'))
                menu = None
                items = None
                if data:
                    menu = data.get('menu', None)
                if menu:
                    menu_items = menu.get(h.lang(), None)
    except Exception as e:
        log.error('Exception in csc_main_menu_items: %s', e)
    return menu_items

def csc_footer_menu_items():
    '''
    Returns data for footer menu items 
    Get data of endpoint set in ckanext.csc.footer.menu.items config property
    '''
    data = None
    menu_items = None
    try:
        url = _csc_get_filepath(config.get('ckanext.csc.footer.menu.items', None))
        if url:
            response = urllib.urlopen(url)
            if response:
                data = json.loads(response.read())
                if data:
                    menu = data.get('menu', None)
                    if menu:
                        menu_items = menu.get(h.lang(), None)
    except Exception as e:
        log.error('Exception in csc_footer_menu_items: %s', e)
    return menu_items
    



##################################
## METODOS PARA CUADRO DE MANDO ##
##################################

def csc_dashboard_get_month(month = None, day=0):
    result = month
    if month:
        if month == 'All':
            result = _('All months')
        else:
            d = strptime(month, '%Y-%m')
            month_name = '%s %s' % (_(calendar.month_name[d.tm_mon]), d.tm_year)
            end = calendar.monthrange(d.tm_year, d.tm_mon)[1]
            if day > 0 and day < end:
                result =  '%s (%s %s)' % (month_name, _('up to'), day)
            else:
                result = '%s' %  _(month_name)
    return result


def _csc_dashboard_convert_date(sdate=None):
    fdate = None
    if sdate:
        try:
            data_date = datetime.datetime.strptime(sdate, '%Y-%m-%d')
            language = csh.lang()
            if language == 'en':
                fdate = data_date.strftime('%m-%d-%Y')
            else:
                fdate = data_date.strftime('%d/%m/%Y')
        except:
            data_date = None
    return fdate


def _csc_dashboard_theme_label(theme=None):
    '''
    Given an theme, get its label

    :param theme: format
    :type string
    
    :rtype string
    '''
    if theme:
        dataset = sh.scheming_get_schema('dataset', 'dataset')
        themes = sh.scheming_field_by_name(dataset.get('dataset_fields'),
                'theme')
        theme_label = sh.scheming_choices_label(themes['choices'], theme)
        if theme_label:
            return theme_label
    return theme


def csc_dashboard_data_num_datasets_by_month_year():
    '''
    Returns data for datasets per month chart. 
    Get data of endpoint set in ckanext.csc.dashboard.chart.datasets_month_year.url_data config property
    '''
    data = None
    result_data = []
    try:
        url = _csc_get_filepath(config.get('ckanext.csc.dashboard.chart.datasets_month_year.url_data', None))
        if url:
            response = urllib.urlopen(url)
            if response:
                data = json.loads(response.read())
                if data:
                    for item in data:
                        year = item.get("year", None)
                        value = item.get("value", 0)
                        if year and value:
                            result_data.append({"year" : year, "value": value})
                    return json.dumps(result_data)
    except Exception as e:
        log.error('Exception in csc_dashboard_data_num_datasets_by_month_year: %s', e)
    return []

def csc_dashboard_data_resource_format():
    '''
    Returns data for resource format. 
    Get data of endpoint set in ckanext.csc.dashboard.chart.resource_format.url_data config property
    '''
    data = None
    result_data = []
    total = 0
    data_date = None
    try:
        url = _csc_get_filepath(config.get('ckanext.csc.dashboard.chart.resource_format.url_data', None))
        if url:
            response = urllib.urlopen(url)
            if response:
                data = json.loads(response.read())
        if data:
            available_formats = {}
            for item in data:
                total = total + item.get('value', 0)
                if not data_date:
                    data_date = _csc_dashboard_convert_date(item.get('date', None))
                format = item.get('format', None)
                if format: 
                    if format.lower() not in available_formats:
                        available_formats[format] = csc_resource_format_label(format.lower())
                    result_data.append({"date": item.get('date',''), "format": available_formats.get(format.lower(), format), "value": item.get('value', 0)})
            return json.dumps(result_data), total, data_date
    except Exception as e:
        log.error('Exception in csc_dashboard_data_resource_format: %s', e)
    return [], total, data_date

def csc_dashboard_data_num_datasets_by_category():
    '''
    Returns data for datasets per category chart. 
    Get data of endpoint set in ckanext.csc.dashboard.chart.datasets_category.url_data config property
    '''
    result_data = []
    data = None
    data_date = None
    try:
        url = _csc_get_filepath(config.get('ckanext.csc.dashboard.chart.datasets_category.url_data', None))
        if url:
            response = urllib.urlopen(url)
            if response:
                data = json.loads(response.read())
        if data:
            data_date = None
            for item in data:
                if not data_date:
                    data_date = _csc_dashboard_convert_date(item.get('date', None))
                theme = item.get('theme', None)
                if theme:
                    label_theme = theme 
                    label_theme = _csc_dashboard_theme_label(theme)
                    result_data.append({"date": item.get('date',''), "theme": label_theme, "value": item.get('value', 0)})
            return json.dumps(result_data), data_date
    except Exception as e:
        log.error('Exception in csc_dashboard_data_num_datasets_by_category: %s', e)
    return [], data_date


def csc_dashboard_data_num_visits():
    '''
    Returns data for visits per month. 
    Get data of endpoint set in ckanext.csc.dashboard.chart.visits_month_year.url_data config property
    '''
    data = None
    result_data = []
    try:
        url = _csc_get_filepath(config.get('ckanext.csc.dashboard.chart.visits_month_year.url_data', None))
        if url:
            response = urllib.urlopen(url)
            if response:
                data = json.loads(response.read())
                if data:
                    for item in data:
                        date = item.get("date", None)
                        value = item.get("value", 0)
                        if date and value:
                            result_data.append({"date" : date, "value": value})
                    return json.dumps(result_data)
    except Exception as e:
        log.error('Exception in csc_dashboard_data_num_visits: %s', e)
    return []


def csc_dashboard_data_most_visited_datasets(visible_visits = None):
    '''
    Returns data for the most visited datasets. 
    Get data of endpoint set in ckanext.csc.dashboard.chart.most_visited_datasets.url_data config property
    '''
    data = None
    result_data = []
    if not visible_visits:
        visible_visits = asbool(
            config.get('ckanext.csc.dashboard.chart.most_visited_datasets.num_visits.visible', False))
    month_list = []
    month_name_list = []
    month_name_dict = {}
    column_titles = [_('Month'), _('Order'), _('Dataset'), _('Publisher'), _('Visits')]
    try:
        url = _csc_get_filepath(config.get('ckanext.csc.dashboard.chart.most_visited_datasets.url_data', None))
        if url:
            response = urllib.urlopen(url)
            if response:
                data = json.loads(response.read())
                if data:
                    prefix_url = config.get('ckan.site_url') + h.url_for(controller='package', action='search') + "/"
                    index = prefix_url.find('://')
                    if c.userobj and index >= 0:
                        prefix_url = 'https' + prefix_url[index:] 
                    for item in data:
                        if item:
                            new_item = {}
                            month = item.get('month', None)
                            day = item.get('day', 0)
                            if month:
                                month_name = ''
                                if month and month in month_list:
                                    month_name = month_name_dict.get(month, '')
                                else:
                                    month_list.append(month)
                                    month_name = csc_dashboard_get_month(month, day)
                                    month_name_list.append({"id": month.replace('-', ''), "name": month_name})
                                    month_name_dict[month] = month_name
                                new_item["month"] = month_name
                                new_item["month_id"] = month.replace('-', '')
                                new_item["order"] = item.get('order', '')
                                new_item["url"] = item.get('name', '')
                                new_item["title"] = item.get('title', '')
                                new_item["package"] = "<a href='%s%s'>%s</a>" % (prefix_url, item.get('name', ''), item.get('title', ''))
                                new_item["publisher"] = item.get('publisher', '')
                                if visible_visits:
                                    new_item["visits"] = item.get('visits', 0)
                                result_data.append(new_item)
    except Exception as e:
        log.error('Exception in csc_dashboard_data_most_visited_datasets: %s', e)
        result_data = []
    if result_data and len(result_data) > 0:
        return json.dumps(result_data), json.dumps(month_name_list), month_name_list, json.dumps(column_titles), visible_visits
    else:
        return [], json.dumps(month_name_list), month_name_list, json.dumps(column_titles), visible_visits


def csc_get_visibility_of_public_graphs(graph_names=None):
    visibility = {}
    if graph_names:
        for name in graph_names:
            if name:
                if name == 'chartVisitsByMonth':
                    visibility[name] = asbool(
                                       config.get('ckanext.csc.dashboard.chart.visits_month_year.visible', False))
                elif name == 'chartNumDatasetsByMonthYear':
                    visibility[name] = asbool(
                                       config.get('ckanext.csc.dashboard.chart.datasets_month_year.visible', False))
                elif name == 'chartNumDatasetsByCategory':
                    visibility[name] = asbool(
                                       config.get('ckanext.csc.dashboard.chart.datasets_category.visible', False))
                elif name == 'chartMostVisitedDatasets':
                    visibility[name] = asbool(
                                       config.get('ckanext.csc.dashboard.chart.most_visited_datasets.visible', False))
                elif name == 'chartResourceFormat':
                    visibility[name] = asbool(
                                       config.get('ckanext.csc.dashboard.chart.resource_format.visible', False))
    return visibility

def csc_show_english_values():
    """
    Return a boolean that enables or disables the English values for editors
    """
    english_config = config.get('ckanext.csc.display_english', False)
    visible = True if (english_config and english_config == 'true') else False
    return visible