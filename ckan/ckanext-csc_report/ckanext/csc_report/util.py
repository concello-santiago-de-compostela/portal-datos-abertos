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
 
import logging
import re
import urllib



from sqlalchemy import Table, Column, MetaData, PrimaryKeyConstraint
from sqlalchemy import types
from sqlalchemy.orm import mapper
from sqlalchemy.sql.expression import cast
from sqlalchemy import func
from sqlalchemy.exc import InvalidRequestError

from ckan import model as model
from ckan.model.domain_object import DomainObject
from ckan.model.meta import metadata, Session
from ckanext.csc_report.model import CscGaDataset, CscGaSession, CSC_GA_DATASET_TABLE_NAME, CSC_GA_SESSION_TABLE_NAME


from lib import GaProgressBar
from paste.util.PySourceColor import null

log = logging.getLogger(__name__)



def delete(period_name, object_type):
    '''
    Deletes table data for the specified period, or specify 'all'
    for all periods.
    '''
    if object_type in (CscGaDataset, CscGaSession):
        q = model.Session.query(object_type)
        if period_name != 'All':
            q = q.filter_by(period_name=period_name)
        q.delete()
        model.repo.commit_and_remove()

def pre_update_csc_ga_dataset_stats(period_name):
    q = model.Session.query(CscGaDataset).\
        filter(CscGaDataset.year_month==period_name)
    log.debug("Deleting %d '%s' %s records" % (q.count(), period_name, CSC_GA_DATASET_TABLE_NAME))
    print ("Deleting %d '%s' %s records" % (q.count(), period_name, CSC_GA_DATASET_TABLE_NAME))
    q.delete()

    model.Session.flush()
    model.Session.commit()
    model.repo.commit_and_remove()
    log.debug('...done')
    print '...done'

def pre_update_csc_ga_session_stats(period_name):
    q = model.Session.query(CscGaSession).\
        filter(CscGaSession.year_month==period_name)
    log.debug("Deleting %d '%s' %s records" % (q.count(), period_name, CSC_GA_SESSION_TABLE_NAME))
    print ("Deleting %d '%s' %s records" % (q.count(), period_name, CSC_GA_SESSION_TABLE_NAME))
    q.delete()

    model.Session.flush()
    model.Session.commit()
    model.repo.commit_and_remove()
    log.debug('...done')
    print '...done'

def _get_previous_csc_ga_dataset_stats(url):
    dat_name = None
    org_id = None
    if url:
        try:
            query = '''select distinct dataset_name
                       from csc_ga_datasets
                       where dataset_name like '{p0}'
                       and year_month not like 'All';'''.format(p0=url)

            result = model.Session.execute(query)
            row_count = 0
            if result:
                for row in result:
                    row_count = row_count + 1
                    if row_count == 1:
                        dat_name = row[0]
                        org_id = row[1]

                    if row_count > 2:
                        print ("WARNING url {} -> Found {} distinct values for (dataset_name, organization_id)".format(url, row_count))
                    if row_count == 0:
                        print ("WARNING url {} -> Not found values for (dataset_name, organization_id)".format(url))
        except Exception as e:
            print "Exception {}"
            print str(e)
            try:
                print "EXCEPTION pack_url {} -> Exception {}".format(url, str(e))
            except:
                print "Exception {}".format(str(e))

    return dat_name, org_id


def update_csc_ga_dataset_stats(period_name, period_complete_day, url_data, print_progress=False):
    '''
    Given a list of urls and number of hits for each during a given period,
    stores them in CscGaDataset under the period.
    '''
    print "Updating csc_ga_dataset..."
    progress_total = len(url_data)
    progress_count = 0
    if print_progress:
        progress_bar = GaProgressBar(progress_total)
    urls_in_csc_ga_dataset_this_period = set(
        result[0] for result in model.Session.query(CscGaDataset.dataset_name)
                                     .filter(CscGaDataset.year_month==period_name)
                                     .all())
    processed_urls = []
    #dict with key:<url> and value: (<dataset_name>, <org_id>, <pub_id>)
    processed_urls_dict = {} 
    orgs = {}
    for url, views in url_data:
        progress_count += 1
        if print_progress:
            progress_bar.update(progress_count)

        if url in urls_in_csc_ga_dataset_this_period:
            item = model.Session.query(CscGaDataset).\
                filter(CscGaDataset.year_month==period_name).\
                filter(CscGaDataset.dataset_name==url).first()
            item.pageviews = int(item.pageviews or 0) + int(views or 0)
            model.Session.add(item)
        else:
            print url
            dataset_name = None
            org_id = None
            dataset = model.Package.get(url)
            if dataset:
                dataset_name = dataset.name
                org_id = dataset.owner_org
            #Only if dataset not found, possible purged dataset, check previous stats
            if dataset_name is None:
                #get persisted data from other periods
                if url not in processed_urls:
                    dataset_name, org_id = _get_previous_csc_ga_dataset_stats(url)
                    processed_urls.append(url)
                    processed_urls_dict[url] = (dataset_name, org_id)
                else:
                    url_dict = processed_urls_dict.get(url, None)
                    if url_dict:
                        dataset_name = url_dict[0]
                        org_id = url_dict[1]

            if dataset_name :
                values = {
                        'year_month': period_name,
                        'end_day': period_complete_day,
                        'pageviews': views,
                        'dataset_name': dataset_name
                        }
                model.Session.add(CscGaDataset(**values))
                urls_in_csc_ga_dataset_this_period.add(url)
        model.Session.commit()
    print "...Updated csc_ga_dataset"

def update_csc_ga_session_stats(period_name, period_complete_day, data,
                     print_progress=False):
    '''
    Given a list of sections and number of sessions for each during a given period,
    stores them in CscGaSession under the period.
    '''
    print "Updating csc_ga_sessions..."
    progress_total = len(data)
    progress_count = 0
    if print_progress:
        progress_bar = GaProgressBar(progress_total)
    for sessions in data:
        progress_count += 1
        if print_progress:
            progress_bar.update(progress_count)
        values = {
                  'year_month': period_name,
                  'end_day': period_complete_day,
                  'sessions': sessions
                 }
        model.Session.add(CscGaSession(**values))
        model.Session.commit()
    print "... Updated csc_ga_sessions"

def post_update_csc_ga_dataset_stats():

    """ Check the distinct url field in csc_ga_dataset and make sure
        it has an All record.  If not then create one.

        After running this then every URL should have an All
        record regardless of whether the URL has an entry for
        the month being currently processed.
    """
    q = model.Session.query(CscGaDataset).\
        filter_by(year_month='All')
    log.debug("Deleting %d 'All' csc_ga_dataset records..." % q.count())
    print ("Deleting %d 'All' csc_ga_dataset records..." % q.count())
    q.delete()

    # For dataset URLs:
    # Calculate the total views/visits for All months
    log.debug('Calculating CscGaDataset "All" records')
    print 'Calculating CscGaDataset "All" records'
    query = '''select dataset_name, sum(pageviews::int)
               from csc_ga_datasets
               where dataset_name != ''
               group by dataset_name
               order by sum(pageviews::int) desc
               '''
    res = model.Session.execute(query).fetchall()

    for dataset_name, views in res:
        values = {
            'year_month': "All",
            'end_day': 0,
            'pageviews': views,
            'dataset_name': dataset_name
        }
        model.Session.add(CscGaDataset(**values))
        model.Session.commit()

    log.debug('... Created csc_ga_dataset "All" records')
    print '... Created csc_ga_dataset "All" records'