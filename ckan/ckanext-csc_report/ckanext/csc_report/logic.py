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
import re
import json

from ckan.plugins import toolkit
from ckan.plugins.toolkit import config, _, c
from dateutil.parser import parse as dateutil_parse
from ckanext.csc_report.commands import FILENAME_REGEX

import logging
log = logging.getLogger(__name__)

def csc_report_update_published_datasets(context, data_dict):
    '''
    Update csc_published_datasets table
    adding num total created datasets before given date param

    :param date: the creation date of datasets must be before this
    :type date: string
    
    :param import_date: year-month of creation date of datasets
    :type import_date: string
    
    :param save: True only if update database, False if only print
    :type save: boolean.
    '''

    toolkit.check_access('csc_report_update_published_datasets', context, data_dict)

    date = data_dict.get('date')
    import_date = data_dict.get('import_date')
    save = data_dict.get('save', False)

    model = context['model']
    results = []
    log.debug("Getting total data ....")
    # total active, public dataset pusblished before than {p0} date
    sql = '''select count(*) from 
             (select h.* from (select ROW_NUMBER() OVER (PARTITION BY pr.continuity_id order by pr.revision_timestamp asc) as rn, * from package_revision pr 
             where pr.revision_timestamp < '{p0}'::timestamp and pr.type like 'dataset') h where h.rn = 1 ) sc, 
             (select h.* from (select ROW_NUMBER() OVER (PARTITION BY pr.continuity_id order by pr.revision_timestamp desc) as rn, * from package_revision pr 
             where pr.revision_timestamp < '{p0}'::timestamp and pr.type like 'dataset') h 
             where h.rn = 1 and h.state like 'active'
             and h.private = false and h.expired_timestamp >=  '{p0}'::timestamp) slu 
             where sc.continuity_id = slu.continuity_id;'''.format(p0=date)
    result = model.Session.execute(sql)
    value = result.fetchone()[0]
    results.append((import_date, value))
    result = model.Session.execute(sql)
    if save:
        # check if there are saved data from this {p0} date
        sql = '''select count(*) from csc_published_datasets
                 where year_month like '{p0}';'''.format(p0=import_date)
        result = model.Session.execute(sql)
        total = result.fetchone()[0]
        log.debug("Updating data...")
        sql = '''begin;'''
        if total > 0:
            sql += '''DELETE FROM csc_published_datasets where year_month like '{p0}';'''.format(p0=import_date)
        for result in results:
            sql += '''INSERT INTO csc_published_datasets (year_month, num_datasets)
                      VALUES ('{p1}', '{p2}');'''.format(p1 = result[0], p2 = result[1])
        sql += '''
                commit;
               '''
        model.Session.execute(sql)
    else:
        print "Results: "
        for row in results:
            print row
    

def _get_complete_filename(destination=None, name=None, extension = 'json'):
    
    if destination is None or len(destination) == 0 or len(destination.strip(' \t\n\r')) == 0:
        log.info('No destination directory')
        return None
    else:
        destination = destination.strip(' \t\n\r')
        if destination[-1] == '/':
           destination = destination[:-1]

    if name and len(name) > 0 and len(name.strip(' \t\n\r')) > 0:
        name = name.strip(' \t\n\r')
        pattern = re.compile(FILENAME_REGEX)
        if not pattern.match(name):
            log.info('No valid filename')
            return None
    else:
        name = None
    filename = destination + '/' + name  + '.' + extension
    return filename

def _write_file(filedata=None, destination=None, filename=None, extension = 'json'):

    if filedata is None:
        log.info('No data for write in file')
        return None
    complete_filename = _get_complete_filename(destination, filename, extension)
    if complete_filename:
        try:
            outfile = open(complete_filename, 'w')
            try:
                outfile.write(filedata)
                outfile.close()
            except Exception as e:
                log.error('Exception %s', e)
                complete_filename = None
            finally:
                outfile.close()
        except Exception as e:
            log.error('Exception %s', e)
            complete_filename = None
    return complete_filename


def _execute_fetchone_sql(model=None, sql=None):
    if sql and model:
        try:
            result = model.Session.execute(sql)
            print result
            row = result.fetchone() if result else None
            if row and len(row) > 0:
                return row[0]
        except Exception as e:
            log.error('Exception %s', e)
            return None
    return None

def csc_report_json_published_datasets(context, data_dict):
    '''
    Get csc_report_json_published_datasets table data and write json files

    :param destination: directory destination of json file
    :type destination: string

    :param prefix: filename  of json file
    :type prefix: string
    '''
    toolkit.check_access('csc_report_json_published_datasets_auth', context, data_dict)
    destination = data_dict.get('destination')
    filename = data_dict.get('filename')
    model = context['model']

    sql =  '''select concat('[', concat(string_agg(r.dict, ','), ']'))
              from (select concat('{', concat(s.ym, concat(', ', 
              concat(s.value, '}')))) dict from 
              (select concat('"year": "', concat(d.year_month, '"')) as ym, 
              concat('"value": ', d.num_datasets) as value
              from csc_published_datasets d
              order by year_month asc) s)r;'''
    result = _execute_fetchone_sql(model, sql)
    return _write_file(result, destination, filename)


def csc_report_json_current_resource_format(context, data_dict):
    '''
    Get current resource format
    
    :param destination: directory destination of json file
    :type destination: string

    :param prefix: filename  of json file
    :type prefix: string
    '''

    toolkit.check_access('csc_json_current_resource_format_auth', context, data_dict)
    destination = data_dict.get('destination')
    filename = data_dict.get('filename')
    model = context['model']
    sql = '''select concat('[', concat(string_agg(s2.dict, ','), ']')) from
             (select concat('{"date": "', concat((to_char(now(), 'YYYY-MM-DD')), 
              concat('", "format": "', concat(s1.f, concat('", "value": ', 
              concat(s1.num, '}')))))) as dict from (select r.format as f, 
              count(*) num from package p, resource r where
              p.private = False and p.type like 'dataset' 
              and p.state like 'active' and p.id = r.package_id 
              and r.state like 'active' group by f
              order by num desc)s1)s2; '''
    result = _execute_fetchone_sql(model, sql)
    return _write_file(result, destination, filename)

def csc_report_json_current_published_datasets_by_category(context, data_dict):
    '''
    Get current published datasets by category
    
    :param destination: directory destination of json file
    :type destination: string
    
    :param filename: filename of json file
    :type filename: string
    '''

    toolkit.check_access('dge_dashboard_json_current_published_datasets_by_category', context, data_dict)

    destination = data_dict.get('destination')
    filename = data_dict.get('filename')

    model = context['model']

    sql = '''select concat('[', concat(string_agg(r.dict, ','), ']'))from
             (select concat('{"date": "', concat((to_char(now(), 'YYYY-MM-DD')), 
             concat('", "theme": "', concat(s1.theme, concat('", "value": ', 
             concat(s1.num, '}')))))) as dict from (select s.theme, 
             count(*) as num from (select p.name, 
             regexp_split_to_table(regexp_replace(regexp_replace(regexp_replace(pe.value, '"', '', 'g'), ']' , ''), '\[', ''), E', ') as theme FROM package_extra pe, package p
             where pe.key like 'theme'
             and p.state like 'active'
             and p.private = false
             and pe.package_id  = p.id
             order by package_id) as s
             group by theme order by count(*) desc) as s1)as r;'''

    result = _execute_fetchone_sql(model, sql)
    return _write_file(result, destination, filename)

def csc_report_json_sessions(context, data_dict):
    '''
    Get general sessions to portal 
    
    :param destination: directory destination of json file
    :type destination: string
    
    :param filename: filename of json file
    :type filename: string

    '''

    toolkit.check_access('csc_report_json_sessions_auth', context, data_dict)

    destination = data_dict.get('destination')
    filename = data_dict.get('filename')

    model = context['model']

    sql = '''select concat('[', concat(string_agg(s.dict, ','), ']'))from
                 (select concat('{"date": "', concat(year_month, 
                 concat('", "value": ', concat(sessions, '}')))) as dict
                 from csc_ga_sessions
                 order by year_month asc)s;'''


    result = _execute_fetchone_sql(model, sql)
    return _write_file(result, destination, filename)


def csc_report_json_visited_datasets(context, data_dict):
    '''
    Get general visits to datasets 
    
    :param destination: directory destination of json file
    :type destination: string
    
    :param filename: filename of json file
    :type filename: string
    '''

    toolkit.check_access('csc_report_json_visited_datasets_auth', context, data_dict)

    destination = data_dict.get('destination')
    filename = data_dict.get('filename')

    model = context['model']
    results = []
    string_result = None

    year_month_day_list = []
    sql = '''select distinct year_month, end_day from csc_ga_datasets
             order by year_month desc;'''
    result = model.Session.execute(sql)
    if result:
        for row in result:
            year_month_day_list.append({'y_m':row[0], 'day': row[1]})
    if year_month_day_list:
        for item in year_month_day_list:
            y_m = item.get('y_m', '')
            day = item.get('day', 0)
            sql = '''select concat('"month": "', concat(s1.year_month, 
                         concat('", "day": ', concat(s1.end_day, 
                         concat(', "name": "', concat(p.name, 
                         concat('", "title": "', concat(replace(p.title, '"', E'\\''), 
                         concat('", "publisher": "', concat(g.title, 
                         concat('", "visits": ', s1.pageviews))))))))))) as dict from 
                         package p, "group" g, (select year_month, end_day, 
                         dataset_name, pageviews from 
                         csc_ga_datasets where year_month like '{p0}')s1
                         where p.name = s1.dataset_name
                         and g.id like p.owner_org
                         order by s1.pageviews desc, p.title asc
                          limit 10;'''.format(p0=y_m)

            result = model.Session.execute(sql)
            if result:
                i = 1
                for row in result:
                    results.append('{"order": %s, %s}' % (i, row[0]))
                    i = i+1

    string_result = "[" + ",".join(results) + "]"
    string_result = string_result.encode('utf-8')
  
    return _write_file(string_result, destination, filename)

############### AUTHORIZATION ###################

def user_is_sysadmin(context):
    '''
        Checks if the user defined in the context is a sysadmin
        rtype: boolean
    '''
    model = context['model']
    user = context['user']
    user_obj = model.User.get(user)
    if not user_obj:
        log.warn('User %s not found').format(user)
    return user_obj.sysadmin if user_obj else False

@toolkit.auth_allow_anonymous_access
def csc_report_auth(context, data_dict):
    '''
    All users can access  by default
    '''
    return {'success': True}

def csc_report_is_sysadmin_auth(context, data_dict):
    '''
        Only sysadmins can do it
    '''
    if not user_is_sysadmin(context):
        return {'success': False, 'msg': 'Only sysadmins can do this operation'}
    else:
        return {'success': True}

def csc_report_json_published_datasets_auth(context, data_dict):
    '''
        Authorization check for get csc_published_dataset table data

        Only sysadmins can do it
    '''
    if not user_is_sysadmin(context):
        return {'success': False, 'msg': _('Only sysadmins can get number of historical published datasets')}
    else:
        return {'success': True}

def csc_report_json_current_resource_format_auth(context, data_dict):
    '''
        Authorization check for get resource by format

        Only sysadmins can do it
    '''
    if not user_is_sysadmin(context):
        return {'success': False, 'msg': _('Only sysadmins can get number of resource by format')}
    else:
        return {'success': True}

def csc_report_json_current_published_datasets_by_category_auth(context, data_dict):
    '''
        Authorization check for get published datasets by category

        Only sysadmins can do it
    '''
    if not user_is_sysadmin(context):
        return {'success': False, 'msg': _('Only sysadmins can get number of published datasets by category')}
    else:
        return {'success': True}

def csc_report_json_sessions_auth(context, data_dict):
    '''
        Authorization check for get sessions to portal

        Only sysadmins can do it
    '''
    if not user_is_sysadmin(context):
        return {'success': False, 'msg': _('Only sysadmins can get sessions')}
    else:
        return {'success': True}

def csc_report_json_visited_datasets_auth(context, data_dict):
    '''
        Authorization check for get published datasets visits

        Only sysadmins can do it
    '''
    if not user_is_sysadmin(context):
        return {'success': False, 'msg': _('Only sysadmins can get number of published datasets visits')}
    else:
        return {'success': True}



