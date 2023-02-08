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
 
import os
import re
import logging
import datetime
import time
import sys


from ckan.plugins.toolkit import config, CkanCommand, get_action
from datetime import datetime
import ckan.model as model
from ckanext.csc_report.ga_download_analytics import CscGaDownloadAnalytics, KIND_STATS, KIND_STAT_DATASETS, KIND_STAT_VISITS




log = logging.getLogger(__name__)

DEFAULT_DATASET_URL_PREFIX = '/catalogo/' 
DEFAULT_DATASET_URL = '/dataset/' 
DEFAULT_RESOURCE_URL_TAG = '/downloads/'
DEFAULT_URL_LANGUAGE_PREFIX_REGEX = '(|/es|/gl)'
DEFAULT_URL_VALID_NAME_REGEX = '[a-z0-9-_]+'
FILENAME_REGEX = '^[a-zA-Z0-9][a-zA-Z0-9_-]+[a-zA-Z0-9]$'


class CscReportCommand(CkanCommand):

    def __init__(self,name):
        super(CscReportCommand,self).__init__(name)

    def _load_config(self):
        super(CscReportCommand, self)._load_config()

    def _set_context(self):
        # We'll need a sysadmin user to perform most of the actions
        # We will use the sysadmin site user (named as the site_id)
        context = {'model':model,'session':model.Session,'ignore_auth':True}
        admin_user = get_action('get_site_user')(context,{})
        context = {
                'model':model,
                'session':model.Session,
                'user': admin_user['name'],
                'ignore_auth': True,
                }
        return context

    def _validate_args(self, args = [], method_log_prefix = ''):
        for_date = None
        save = False
        time_period = None
        if len(self.args) == 2:
            dtype = self.args[0]
            if dtype != 'save' and dtype != 'print':
                print '%s Please provide a valid type (save or print)' % (method_log_prefix)
                sys.exit()
            else:
                if dtype == 'save':
                    save = True

            time_period = self.args[1]
            if time_period == 'latest':
                time_period = datetime.now().strftime("%Y-%m")
            elif time_period == 'last_month':
                now = datetime.now()
                if now.month == 1:
                    last_month = datetime(now.year-1, 12, 1, 0, 0, 0)
                else:
                    last_month = datetime(now.year, now.month-1, 1, 0, 0, 0)
                time_period = last_month.strftime("%Y-%m")
                
            try:
                for_date = datetime.strptime(time_period, '%Y-%m')
            except ValueError as e:
                print '%s Please provide a valid time period param (latest|YYYY-MM|last_month)' % (method_log_prefix)
                sys.exit(1)

            if for_date:
                year = for_date.year
                month = for_date.month
            if month == 12:
                calculation_date = datetime(year+1, 1, 1, 0, 0, 0)
            else:
                calculation_date = datetime(year, month+1, 1, 0, 0, 0)
            return save, time_period, calculation_date
        else:
            print '%s Please provide valid params {print|save} {latest|YYYY-MM|last_month}' % (method_log_prefix)
            sys.exit(1)
    
    def get_destination_filename(self, filename):
        destination = config.get('ckanext-csc_report.storage.directory.path', None)
        if filename is None or len(filename) == 0 or len(filename.strip(' \t\n\r')) == 0:
            print 'Please provide a %s' % (filename)
            sys.exit(1)
        else:
            filename = filename.strip(' \t\n\r')
            pattern = re.compile(FILENAME_REGEX)
            if not pattern.match(filename):
                print 'Please provide a valid %s. Regular expression: %s' % (filename, FILENAME_REGEX)
        return destination, filename


########################################################
#### COMANDO PARA LA ACTUALIZACION DE BASE DE DATOS ####
########################################################

class CscReportInitDB(CscReportCommand):
    """Initialise the custom local stats database tables
    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 0
    min_args = 0
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'

    def command(self):
        
        init = datetime.now()
        s_args = (self.args if self.args else '(no args)')
        print '[%s] - Init CscReportInitDB command with args: %s.' % (init.strftime(CscReportInitDB.datetime_format), s_args)
        try:
            self._load_config()
            model.Session.remove()
            model.Session.configure(bind=model.meta.engine)
            from ckanext.csc_report import model as csc_model
            csc_model.init_tables()
            log.info("Set up custom statistics tables in main database")
        except Exception as e:
            print 'Exception %s' % e
            sys.exit(1)
        finally:
            end = datetime.now()
            print '[%s] - End CscReportInitDB command with args %s. Executed command in %s milliseconds.' % (end.strftime(CscReportInitDB.datetime_format), s_args, (end-init).total_seconds()*1000)
        sys.exit(0)

###########################################################
#### COMANDOS PARA LA ACTUALIZACION DE DATOS DE TABLAS ####
###########################################################

class CscReportLoadAnalytics(CscReportCommand): 
    def __init__(self, name):
        super(CscReportLoadAnalytics, self).__init__(name)
        from ga_download_analytics import DATASET_STAT, VISIT_STAT
        self.stat_names = (DATASET_STAT, VISIT_STAT, 'csc_ga')
        self.parser.add_option('-d', '--delete-first',
                               action='store_true',
                               default=False,
                               dest='delete_first',
                               help='Delete data for the period first')
        self.parser.add_option('-s', '--stat',
                               metavar="STAT",
                               dest='stat',
                               help='Only calulcate a particular stat (or collection of stats)- one of: %s' %
                                    '|'.join(self.stat_names))
    

    def _execute_command(self, kind_stats = None):
        

        self._load_config()
        self.resource_url_tag = config.get('googleanalytics_resource_prefix', DEFAULT_RESOURCE_URL_TAG)
        self.dataset_url = config.get('ckanext-csc_report.dataset_url', DEFAULT_DATASET_URL)
        
        self.dataset_url_prefixs = []
        string_dataset_url_prefix = config.get('ckanext-csc_report.dataset_url.prefix', [DEFAULT_DATASET_URL_PREFIX, DEFAULT_URL_LANGUAGE_PREFIX_REGEX])
        if string_dataset_url_prefix:
            self.dataset_url_prefixs = string_dataset_url_prefix.split()
        
        self.language_prefix_regex = config.get('ckanext-csc_report.url.language_prefix.regex', DEFAULT_URL_LANGUAGE_PREFIX_REGEX)
        self.valid_name_regex = config.get('ckanext-csc_report.url.valid_name.regex', DEFAULT_URL_VALID_NAME_REGEX)
        self.dataset_url_regex = config.get('ckanext-csc_report.url.dataset.regex', get_dataset_url_regex(self.language_prefix_regex, self.dataset_url, self.valid_name_regex))
        self.exclude_dataset_url_regex = []
        string_exclude_url = config.get('ckanext-csc_report.url.dataset.regex.exclude', None)
        if string_exclude_url:
            self.exclude_dataset_url_regex = string_exclude_url.split()
        self.exclude_visits_url_regex = []
        string_exclude_url = config.get('ckanext-csc_report.url.visits.regex.exclude', None)
        if string_exclude_url:
            self.exclude_visits_url_regex = string_exclude_url.split()


        save, time_period, calculation_date = self._validate_args(self.args, type(self).__name__)
        limit_date_ga4 = datetime(int(config.get('googleanalytics.date.ga4.year', None)), int(config.get('googleanalytics.date.ga4.month', None)), 2, 0, 0, 0)
        self.is_ga4 = limit_date_ga4 < calculation_date

        from ga_auth import (init_service, get_profile_id)
        ga_credentials_file_filepath = config.get('ckanext-csc_report.credentials_file.filepath', '')
        if not ga_credentials_file_filepath or not os.path.exists(ga_credentials_file_filepath):
            print 'ERROR: In the CKAN config you need to specify the filepath of the ' \
                  'Google Analytics credentials file under key: ckanext-csc_report.credentials_file.filepath'
            sys.exit(1)
            
        try:
            self.service = init_service(ga_credentials_file_filepath, self.is_ga4)
        except TypeError as e:
            error_msg = 'Unable to create a service: {0} '\
                        'Have you correctly specified the correct token file in the CKAN config under ' \
                        '"ckanext-csc_report.credentials_file.filepath"?'.format(e)
            print error_msg
            sys.exit(1)
        
        if self.is_ga4 :
           self.profile_id = ""
        else:
           self.profile_id = get_profile_id(self.service)

        self.downloader = CscGaDownloadAnalytics(service=self.service,
                                           profile_id = self.profile_id,
                                           delete_first=self.options.delete_first,
                                           stat=self.options.stat,
                                           print_progress=True,
                                           kind_stats = kind_stats,
                                           save_stats = save,
                                           dataset_url= self.dataset_url,
                                           dataset_url_prefixs = self.dataset_url_prefixs,
                                           dataset_complete_url = self.dataset_url_regex,
                                           dataset_exclude_url= self.exclude_dataset_url_regex,
                                           visits_exclude_url = self.exclude_visits_url_regex,
                                           is_ga4 = self.is_ga4)

        if time_period == 'latest':
            self.downloader.latest()
        elif time_period == 'last_month':
            now = datetime.now()
            if now.month == 1:
                last_month = datetime(now.year-1, 12, 1, 0, 0, 0)
            else:
                last_month = datetime(now.year, now.month-1, 1, 0, 0, 0)
            self.downloader.specific_month(last_month)
        else:
            # The month to use
            for_date = datetime.strptime(time_period, '%Y-%m')
            self.downloader.specific_month(for_date)


class CscReportLoadAnalyticsSessions(CscReportLoadAnalytics):
    """Update csc_ga_sessions from Google Analytics API and store it
    in the csc_model

    Usage: paster csc_sessions <save|print> <time-period>

    Where:
    
      <save-print> is:
        save        - save data in database
        print       - print data in console, not save in database

      <time-period> is:
        latest      - (default) just the 'latest' data
        YYYY-MM     - just data for the specific month
        last_month  - just data for tha last month

    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 2
    min_args = 2
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'



    def command(self):
        """Grab raw data from Google Analytics and save to the database"""
        init = datetime.now()
        s_args = (self.args if self.args else '(no args)')
        print '[%s] - Init CscLoadAnalyticsSessions command with args: %s.' % (init.strftime(CscReportLoadAnalyticsSessions.datetime_format), s_args)
        try:
            self._execute_command(KIND_STAT_VISITS)
        except Exception as e:
            print 'Exception %s' % e
            sys.exit(1)
        finally:
            end = datetime.now()
            print '[%s] - End CscGaReportLoadAnalytics command with args %s. Executed command in %s milliseconds.' % (end.strftime(CscReportLoadAnalyticsSessions.datetime_format), s_args, (end-init).total_seconds()*1000)
        sys.exit(0)

class CscReportLoadAnalyticsDatasetVisits(CscReportLoadAnalytics):
    """Update csc_ga_datasets from Google Analytics API and store it
    in the csc_model

    Usage: paster csc_dataset_visits <save|print> <time-period>

    Where:
    
      <save-print> is:
        save        - save data in database
        print       - print data in console, not save in database
      <time-period> is:
        latest      - (default) just the 'latest' data
        YYYY-MM     - just data for the specific month
        last_month  - just data for tha last month

    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 2
    min_args = 2
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'

    def command(self, ):
        """Grab raw data from Google Analytics and save to the database"""
        init = datetime.now()
        s_args = (self.args if self.args else '(no args)')
        print '[%s] - Init CscGaReportLoadAnalytics command with args: %s.' % (init.strftime(CscReportLoadAnalyticsDatasetVisits.datetime_format), s_args)
        try:
            self._execute_command(KIND_STAT_DATASETS)
        except Exception as e:
            print 'Exception %s' % e
            sys.exit(1)
        finally:
            end = datetime.now()
            print '[%s] - End CscGaReportLoadAnalytics command with args %s. Executed command in %s milliseconds.' % (end.strftime(CscReportLoadAnalyticsDatasetVisits.datetime_format), s_args, (end-init).total_seconds()*1000)
        sys.exit(0)

    
class CscReportLoadPublishedDatasets(CscReportCommand):
    """ Updates csc_published_datasets table with 
        public and active datasets created until and during the given month.
        Options:
        {save|print} {lastest|YYYY-MM|last_month} use ckan internal tracking tables
            {save|print}: save if save data in database; print if only print data, not save in database
            {lastest|YYYY-MM|last_month}: just data for...
                 actual month if None
                 specific month if YYYY-MM
                 last month if last_month
    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 2
    min_args = 0
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'

    def command(self):
        init = datetime.now()
        s_args = (self.args if self.args else '(no args)')
        print '[%s] - Init CscLoadPublishedDatasetsCommand command with args: %s.' % (init.strftime(CscReportLoadPublishedDatasets.datetime_format), s_args)
        try:
            self._load_config()  
            context = self._set_context()
            #log.info('context %s' % context)
            if len(self.args) == 0 or len(self.args) > 2:
                self.parser.print_usage()
                sys.exit(1)
            save, time_period, calculation_date = self._validate_args(self.args, type(self).__name__)
            get_action('csc_report_update_published_datasets')(context,{'date': str(calculation_date), 'import_date': time_period, 'save': save})
            if save:
                print 'Updated csc_published_datasets table with data of %s' % time_period
            print '%s End method.' % (type(self).__name__)
        except Exception as e:
            print 'Exception %s' % (e)
            sys.exit(1)
        finally:
            end = datetime.now()
            print '[%s] - End DgeDashboardLoadCommand command with args %s. Executed command in %s milliseconds.' % (end.strftime(CscReportLoadPublishedDatasets.datetime_format), s_args, (end-init).total_seconds()*1000)
        sys.exit(0)


######################################################
#### COMANDOS PARA LA GENERACION DE FICHEROS JSON ####
######################################################

class CscReportJsonPublishedDatasets(CscReportCommand):
    ''' Generate json file with csc_published_datasets table data
        Options:
           {filename}: The complete filename will be {filename}.json
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 1
    min_args = 1
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'

    def __init__(self,name):
        super(CscReportJsonPublishedDatasets,self).__init__(name)


    def command(self):
        init = datetime.now()
        s_args = (self.args if self.args else '(no args)')
        print '[%s] - Init CscReportJsonPublishedDatasets command with args: %s.' % (init.strftime(CscReportJsonPublishedDatasets.datetime_format), s_args)
        try:
            self._load_config()  
            context = self._set_context()
            #log.info('context %s' % context)
            if len(self.args) == 1:
                filename = self.args[0]
                destination, filename = self.get_destination_filename(filename)
                outfilename = get_action('csc_report_json_published_datasets')(context,{'destination': destination, 'filename': filename})
                if outfilename:
                    print 'Writed json in %s' % (outfilename)
                else:
                    print 'No file was created'
            else:
                print 'Please provide valid filename param'
                sys.exit(1)
        except Exception as e:
            print 'Exception %s' % e
            sys.exit(1)
        finally:
            end = datetime.now()
            print '[%s] - End CscReportJsonPublishedDatasets command with args %s. Executed command in %s milliseconds.' % (end.strftime(CscReportJsonPublishedDatasets.datetime_format), s_args, (end-init).total_seconds()*1000)
        sys.exit(0)

class CscReportJsonResourceFormat(CscReportCommand):
    ''' Generate json file with current number of reource format
        Options:
           {filename}: The complete filename will be {filename}.json
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 1
    min_args = 1
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'

    def __init__(self,name):
        super(CscReportJsonResourceFormat,self).__init__(name)


    def command(self):
        init = datetime.now()
        s_args = (self.args if self.args else '(no args)')
        print '[%s] - Init CscReportJsonResourceFormat command with args: %s.' % (init.strftime(CscReportJsonResourceFormat.datetime_format), s_args)
        try:
            self._load_config()  
            context = self._set_context()
            #log.info('context %s' % context)
            if len(self.args) == 1:
                filename = self.args[0]
                destination, filename = self.get_destination_filename(filename)
                outfilename = get_action('csc_report_json_current_resource_format')(context,{'destination': destination, 'filename': filename})
                if outfilename:
                    print 'Writed json in %s' % (outfilename)
                else:
                    print 'No file was created'
            else:
                print 'Please provide valid filename param'
                sys.exit(1)
        except Exception as e:
            print 'Exception %s' % e
            sys.exit(1)
        finally:
            end = datetime.now()
            print '[%s] - End CscReportJsonResourceFormat command with args %s. Executed command in %s milliseconds.' % (end.strftime(CscReportJsonResourceFormat.datetime_format), s_args, (end-init).total_seconds()*1000)
        sys.exit(0)

class CscReportJsonPublishedDatasetsByCategory(CscReportCommand):
    ''' Generate json file with csc_published_datasets table data
        Options:
           {filename}: The complete filename will be {filename}.json
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 1
    min_args = 1
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'

    def __init__(self,name):
        super(CscReportJsonPublishedDatasetsByCategory,self).__init__(name)


    def command(self):
        init = datetime.now()
        s_args = (self.args if self.args else '(no args)')
        print '[%s] - Init CscReportJsonPublishedDatasetsByCategory command with args: %s.' % (init.strftime(CscReportJsonPublishedDatasetsByCategory.datetime_format), s_args)
        try:
            self._load_config()  
            context = self._set_context()
            #log.info('context %s' % context)
            if len(self.args) == 1:
                filename = self.args[0]
                destination, filename = self.get_destination_filename(filename)
                outfilename = get_action('csc_report_json_current_published_datasets_by_category')(context,{'destination': destination, 'filename': filename})
                if outfilename:
                    print 'Writed json in %s' % (outfilename)
                else:
                    print 'No file was created'
            else:
                print 'Please provide valid filename param'
                sys.exit(1)
        except Exception as e:
            print 'Exception %s' % e
            sys.exit(1)
        finally:
            end = datetime.now()
            print '[%s] - End CscReportJsonPublishedDatasetsByCategory command with args %s. Executed command in %s milliseconds.' % (end.strftime(CscReportJsonPublishedDatasetsByCategory.datetime_format), s_args, (end-init).total_seconds()*1000)
        sys.exit(0)

class CscReportJsonPortalSessions(CscReportCommand):
    ''' Generate json file with csc_ga_session table data
        Options:
           {filename}: The complete filename will be {filename}.json
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 1
    min_args = 1
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'

    def __init__(self,name):
        super(CscReportJsonPortalSessions,self).__init__(name)


    def command(self):
        init = datetime.now()
        s_args = (self.args if self.args else '(no args)')
        print '[%s] - Init CscReportJsonPortalSessions command with args: %s.' % (init.strftime(CscReportJsonPortalSessions.datetime_format), s_args)
        try:
            self._load_config()  
            context = self._set_context()
            #log.info('context %s' % context)
            if len(self.args) == 1:
                filename = self.args[0]
                destination, filename = self.get_destination_filename(filename)
                outfilename = get_action('csc_report_json_sessions')(context,{'destination': destination, 'filename': filename})
                if outfilename:
                    print 'Writed json in %s' % (outfilename)
                else:
                    print 'No file was created'
            else:
                print 'Please provide valid filename param'
                sys.exit(1)
        except Exception as e:
            print 'Exception %s' % e
            sys.exit(1)
        finally:
            end = datetime.now()
            print '[%s] - End CscReportJsonPortalSessions command with args %s. Executed command in %s milliseconds.' % (end.strftime(CscReportJsonPortalSessions.datetime_format), s_args, (end-init).total_seconds()*1000)
        sys.exit(0)

class CscReportJsonDatasetsVisits(CscReportCommand):
    ''' Generate json file with csc_ga_datasets table data
        Options:
           {filename}: The complete filename will be {filename}.json
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 1
    min_args = 1
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'

    def __init__(self,name):
        super(CscReportJsonDatasetsVisits,self).__init__(name)


    def command(self):
        init = datetime.now()
        s_args = (self.args if self.args else '(no args)')
        print '[%s] - Init CscReportJsonDatasetsVisits command with args: %s.' % (init.strftime(CscReportJsonDatasetsVisits.datetime_format), s_args)
        try:
            self._load_config()  
            destination = config.get('ckanext-csc_report.storage.directory.path', None)
            context = self._set_context()
            #log.info('context %s' % context)
            if len(self.args) == 1:
                filename = self.args[0]
                destination, filename = self.get_destination_filename(filename)
                outfilename = get_action('csc_report_json_visited_datasets')(context,{'destination': destination, 'filename': filename})
                if outfilename:
                    print 'Writed json in %s' % (outfilename)
                else:
                    print 'No file was created'
            else:
                print 'Please provide valid filename param'
                sys.exit(1)
        except Exception as e:
            print 'Exception %s' % e
            sys.exit(1)
        finally:
            end = datetime.now()
            print '[%s] - End CscReportJsonDatasetsVisits command with args %s. Executed command in %s milliseconds.' % (end.strftime(CscReportJsonDatasetsVisits.datetime_format), s_args, (end-init).total_seconds()*1000)
        sys.exit(0)




def get_dataset_url_regex(language_prefix=DEFAULT_URL_LANGUAGE_PREFIX_REGEX, dataset_url=DEFAULT_DATASET_URL, valid_name_regex = DEFAULT_URL_VALID_NAME_REGEX):
    return ('^' + language_prefix + dataset_url + valid_name_regex + '/?$')

def get_resource_url_regex(language_prefix=DEFAULT_URL_LANGUAGE_PREFIX_REGEX, dataset_url=DEFAULT_DATASET_URL, valid_name_regex = DEFAULT_URL_VALID_NAME_REGEX):
    return ('^' + language_prefix + dataset_url + valid_name_regex + '/resource/(' + valid_name_regex) + ')'


