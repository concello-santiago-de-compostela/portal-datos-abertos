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


from ckan.plugins.toolkit import config
from ckanext.csc_report import util as csc_util
from ckanext.csc_report import model as csc_model



log = logging.getLogger(__name__)

FORMAT_MONTH = '%Y-%m'
MIN_VIEWS = 50
MIN_VISITS = 20

KIND_STAT_DATASETS = 'pages'
KIND_STAT_VISITS = 'sessions'
KIND_STATS = [KIND_STAT_DATASETS, KIND_STAT_VISITS]

DATASET_STAT = 'csc_ga_dataset'
VISIT_STAT = 'csc_ga_session'




class CscGaDownloadAnalytics(object):
    '''Downloads and stores csc analytics info'''
   
    

    def __init__(self, service=None, profile_id=None, 
                 delete_first=False, stat=None, print_progress=False, 
                 kind_stats=None, save_stats=False, 
                 dataset_url=None, dataset_url_prefixs=None,
                 dataset_complete_url=None, dataset_exclude_url = [], 
                 visits_exclude_url = []):
        self.period = config.get('ckanext-csc_report.period', 'monthly')
        self.hostname = config.get('ckanext-csc_report.hostname', None)
        self.dataset_url = dataset_url
        self.dataset_url_prefixs = dataset_url_prefixs
        self.dataset_complete_url_regex = dataset_complete_url
        self.dataset_exclude_url_regex = dataset_exclude_url
        self.visits_exclude_url_regex = visits_exclude_url
        self.service = service
        self.profile_id = profile_id
        self.delete_first = delete_first
        self.stat = stat
        self.print_progress = print_progress
        self.kind_stats = kind_stats
        self.save_stats = save_stats

    def specific_month(self, date):
        import calendar

        first_of_this_month = datetime.datetime(date.year, date.month, 1)
        _, last_day_of_month = calendar.monthrange(int(date.year), int(date.month))
        last_of_this_month = datetime.datetime(date.year, date.month, last_day_of_month)
        # if this is the latest month, note that it is only up until today
        now = datetime.datetime.now()
        if now.year == date.year and now.month == date.month:
            last_day_of_month = now.day
            last_of_this_month = now
        periods = ((date.strftime(FORMAT_MONTH),
                    last_day_of_month,
                    first_of_this_month, last_of_this_month),)
        self.download_and_store(periods)

    def latest(self):
        if self.period == 'monthly':
            # from first of this month to today
            now = datetime.datetime.now()
            first_of_this_month = datetime.datetime(now.year, now.month, 1)
            periods = ((now.strftime(FORMAT_MONTH),
                        now.day,
                        first_of_this_month, now),)
        else:
            raise NotImplementedError
        self.download_and_store(periods)

    @staticmethod
    def get_full_period_name(period_name, period_complete_day):
        if period_complete_day:
            return period_name + ' (up to %ith)' % period_complete_day
        else:
            return period_name

    def download_and_store(self, periods):
        for period_name, period_complete_day, start_date, end_date in periods:
            log.info('Period "%s" (%s - %s)',
                     self.get_full_period_name(period_name, period_complete_day),
                     start_date.strftime('%Y-%m-%d'),
                     end_date.strftime('%Y-%m-%d'))
            print 'period_name=%s' % period_name
            if self.save_stats and self.delete_first:
                object_type = None
                if self.kind_stats == KIND_STAT_DATASETS:
                    object_type = csc_model.CscGaDataset
                elif self.kind_stats == KIND_STAT_VISITS:
                    object_type = csc_model.CscGaSession
                if object_type:
                    log.info('Deleting existing Analytics for this period "%s" ',
                      period_name)
                    csc_util.delete(period_name, object_type)
            if self.stat in (None, DATASET_STAT) and \
               self.kind_stats == KIND_STAT_DATASETS:
                # Clean out old dge_ga_dataset data before storing the new
                stat = DATASET_STAT
                if self.save_stats:
                    csc_util.pre_update_csc_ga_dataset_stats(period_name)
                log.info('Downloading analytics for dataset views')
                data = self.download(start_date, end_date, 
                                     self.dataset_complete_url_regex,  
                                     self.dataset_exclude_url_regex,
                                     stat)
                if data:
                    if self.save_stats:
                        log.info('Storing dataset views (%i rows)', len(data.get(stat, [])))
                        print 'Storing dataset views (%i rows)' % (len(data.get(stat, [])))
                        self.store(period_name, period_complete_day, data, stat)
                        # Create the All records
                        csc_util.post_update_csc_ga_dataset_stats()
                    else:
                        print data
                        print 'The result contains %i rows:' % (len(data.get(stat, [])))
                        for row in data.get(stat):
                            print row

            if self.stat in (None, VISIT_STAT) and \
               self.kind_stats == KIND_STAT_VISITS:
                # Clean out old csc_ga_sessions data before storing the new
                stat = VISIT_STAT
                if self.save_stats:
                    csc_util.pre_update_csc_ga_session_stats(period_name)

                visits = []
                log.info('Downloading analytics for sessions')
                print 'Downloading analytics for sessions'
                data = self.download(start_date, end_date, '', self.visits_exclude_url_regex, stat)
                #print data
                if data:
                    visits.append((data.get(stat, 0)))
                if visits and len(visits) >= 1:
                    if self.save_stats:
                        log.info('Storing session visits (%i rows)', len(visits))
                        print 'Storing session visits (%i rows)' % (len(visits))
                        self.store(period_name, period_complete_day, {stat:visits}, stat)
                    else:
                        print 'The result contains %i rows:' % (len(visits))
                        for row in visits:
                            print row

    def download(self, start_date, end_date, path=None, exludedPaths= None, stat=None):
        '''Get views & visits data for particular paths & time period from GA
        '''
        if start_date and end_date and path is not None and stat:
            if stat not in [DATASET_STAT, VISIT_STAT]:
                return {}
            start_date = start_date.strftime('%Y-%m-%d')
            end_date = end_date.strftime('%Y-%m-%d')
            print 'Downloading analytics for stat %s, since %s, until %s with path %s' %(stat, start_date, end_date, path)

            query = None
            if stat == DATASET_STAT:
                if path:
                    query = 'ga:pagePath=~%s' % path
                metrics = 'ga:pageviews'
                sort = '-ga:pageviews'
                dimensions = "ga:pagePath"
            
            if stat == VISIT_STAT:
                if path:
                    query = 'ga:pagePath=~%s' % path
                metrics = 'ga:sessions'
                sort = '-ga:sessions'
                dimensions = ''

            if exludedPaths:
                for epath in exludedPaths:
                    if query: 
                        query += ';ga:pagePath!~%s' % epath
                    else:
                        query = 'ga:pagePath!~%s' % epath
            if self.hostname:
                if query:
                    query += ';ga:hostname=~%s' % self.hostname
                else:
                    query = 'ga:hostname=~%s' % self.hostname

            # Supported query params at
            # https://developers.google.com/analytics/devguides/reporting/core/v3/reference
            try:
                args = {}
                args["sort"] = sort
                args["dimensions"] = dimensions
                args["start_date"] = start_date
                args["end_date"] = end_date
                args["metrics"] = metrics
                args["ids"] = "ga:" + self.profile_id
                args["filters"] = query
                args["alt"] = "json"
                
                print "args=%s" % args
                
                results = self._get_ga_data(args)
                
                print "results=%s" % results

            except Exception, e:
                log.exception(e)
                print 'EXCEPTION %s' % e
                return dict(url=[])

            log.info('There are %d results', len(results) if results else 0)
            print 'There are %d results' % len(results) if results else 0
            if stat == DATASET_STAT:
                datasets = []
                pattern = re.compile(path)
                excluded_patterns = []
                for regex in exludedPaths:
                    excluded_patterns.append(re.compile(regex))
                for entry in results:
                    (path, pageviews) = entry
                    url = strip_off_url_prefix(path, self.dataset_url_prefixs)  # strips off prefixs 
                    if url.startswith('/'):
                        url = url[1:]
                    '''if not pattern.match(self.dataset_url + url):
                        continue
                    for excluded_pattern in excluded_patterns:
                        if excluded_pattern.match(self.dataset_url + url):
                            continue'''
                    datasets.append( (url, pageviews) ) # Temporary hack
                return {stat:datasets}
            elif stat == VISIT_STAT:
                rows = results if results else None
                print rows
                visits = 0
                if rows and len(rows) >= 1:
                    for entry in rows:
                        if entry:
                            visits = entry[0]
                            break
                return {stat:visits}
        else:
            log.info("Not all parameters were received")
            print ("Not all parameters were received")
            return {}

    def store(self, period_name, period_complete_day, data, stat):
        if self.save_stats:
            if stat and stat == DATASET_STAT and stat in data:
                csc_util.update_csc_ga_dataset_stats(period_name, period_complete_day, data[stat],
                                     print_progress=self.print_progress)

            if stat and stat == VISIT_STAT and stat in data:
                csc_util.update_csc_ga_session_stats(period_name, period_complete_day, data[stat],
                                          print_progress=self.print_progress)

    def _get_ga_data(self, params):
        '''Returns the GA data specified in params.
        Does all requests to the GA API and retries if needed.
        Returns a dict with the data, or dict(url=[]) if unsuccessful.
        '''
        rows = []
        try:
            rows = self._get_ga_data_simple(params)
            return rows
        except DownloadError:
            print 'DownloadError'
            log.info('Will retry requests after a pause')
            time.sleep(300)
            try:
                return self._get_ga_data_simple(params)
            except DownloadError:
                return rows
            except Exception, e:
                log.exception(e)
                log.error('Uncaught exception in get_ga_data_simple (see '
                          'above)')
                return rows
        except Exception, e:
            print 'Esception e=%s' % e
            log.exception(e)
            log.error('Uncaught exception in get_ga_data_simple (see above)')
            return rows
    
    def _get_ga_data_simple(self, params):
        '''Returns the GA data specified in params.
        Does all requests to the GA API.

        Returns a dict with the data, or raises DownloadError if unsuccessful.
        '''
        try: 
            rows = []
            start_index = 1
            max_results = 10000
            # data retrival is chunked
            completed = False
            while not completed:
                results = self.service.data().ga().get(ids=params['ids'],
                                 filters=params['filters'],
                                 dimensions=params['dimensions'],
                                 start_date=params['start_date'],
                                 start_index=start_index,
                                 max_results=max_results,
                                 metrics=params['metrics'],
                                 sort=params['sort'],
                                 end_date=params['end_date'], 
                                 alt=params['alt']).execute()
                result_count = len(results.get('rows', []))
                if result_count < max_results:
                    completed = True
                rows.extend(results.get('rows', []))
                start_index += max_results
                # rate limiting
                time.sleep(0.2)
            return rows
        except Exception, e:
            log.error("Exception getting GA data: %s" % e)
            raise DownloadError()



global host_re
host_re = None


def strip_off_url_prefix(url, prefixs=[]):
    if url and prefixs:
        result = url
        for prefix in prefixs:
            result = re.sub(prefix, '/', result)
            #print 'prefix {0}'.format(prefix)
            #print 'result {0}'.format(result)
        return result
    return url


class DownloadError(Exception):
    pass
