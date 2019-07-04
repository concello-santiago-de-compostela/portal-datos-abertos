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


from lib import GaProgressBar
from paste.util.PySourceColor import null

log = logging.getLogger(__name__)

CSC_GA_DATASET_TABLE_NAME = 'csc_ga_datasets'
CSC_GA_SESSION_TABLE_NAME = 'csc_ga_sessions'
CSC_PUBLISHED_DATASETS_TABLE_NAME = 'csc_published_datasets'

global csc_ga_dataset_table
global csc_ga_session_table
global csc_published_datasets

csc_ga_dataset_table = None
csc_ga_session_table = None
csc_published_datasets = None

metadata = MetaData()

class CscReportError(Exception):
    pass

class CscReportDomainObject(DomainObject):
    '''Convenience methods for searching objects
    '''

    @classmethod
    def filter(cls, **kwds):
        query = Session.query(cls).autoflush(False)
        return query.filter_by(**kwds)

class CscGaDataset(CscReportDomainObject):
    '''
    A CscGaDataset contains information about a dataset: pageviews, date and 
    organization(publisher).
    '''
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return '''<CscGaDataset year_month=%s, end_day=%s, pageviews=%s, 
                  dataset_name=%s>''' % \
               (self.year_month, self.end_day, self.pageviews, 
                self.dataset_name)

    def __str__(self):
        return self.__repr__().encode('ascii', 'ignore')

    @classmethod
    def get(cls, year_month, dataset_name):
        '''Finds a single entity in the register.'''
        kwds = {'year_month': year_month, 
                'dataset_name': dataset_name}
        o = cls.filter(**kwds).first()
        if o:
            return o
        else:
            return None

    @classmethod
    def create(cls, year_month, end_day, pageviews, dataset_name):
        '''
        Helper function to create an csc_ga_dataset and save it.
        '''
        pd = cls(year_month=year_month, end_day=end_day, 
                 pageviews=pageviews, dataset_name=dataset_name)
        try:
            pd.save()
        except InvalidRequestError:
            Session.rollback()
            pd.save()
        finally:
            # No need to alert administrator so don't log as an error
            log_message = '''year_month=%s, end_day=%s, pageviews=%s, 
                          dataset_name=%s''' % \
                          (year_month, end_day, str(pageviews), dataset_name)
            log.debug(log_message)
            print log_message


class CscGaSession(CscReportDomainObject):
    '''
    A CscGaSession contains information about sessions to portal.
    '''
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return '''<CscGaSession year_month=%s, end_day=%s, sessions=%s>''' % \
               (self.year_month, self.end_day, self.sessions)

    def __str__(self):
        return self.__repr__().encode('ascii', 'ignore')

    @classmethod
    def get(cls, year_month, key, key_value):
        '''Finds a single entity in the register.'''
        kwds = {'year_month': year_month}
        o = cls.filter(**kwds).first()
        if o:
            return o
        else:
            return None

    @classmethod
    def create(cls, year_month, end_day, sessions, key, key_value):
        '''
        Helper function to create an csc_ga_session and save it.
        '''
        pd = cls(year_month=year_month, end_day=end_day, 
                 sessions=sessions)
        try:
            pd.save()
        except InvalidRequestError:
            Session.rollback()
            pd.save()
        finally:
            # No need to alert administrator so don't log as an error
            log_message = 'year_month=%s, end_day=%s, sessions=%s' % \
             (year_month, str(end_day), str(sessions)) 
            log.debug(log_message)
            print log_message

class CscPublishedDataset(CscReportDomainObject):
    '''A Csc Published Dataset is essentially a year-month,
       an organization_id(publisher) and a value of published datasets by these
       organization until these year-month.
    '''
    def __repr__(self):
        return '<CscPublishedDataset year-month=%s num_datasets=%s>' % \
               (self.yearMonth, self.num_datasets)

    def __str__(self):
        return self.__repr__().encode('ascii', 'ignore')

    @classmethod
    def get(cls, year_month, key_value):
        '''Finds a single entity in the register.'''
        kwds = {'year_month': year_month, 
                'key_value': key_value}
        o = cls.filter(**kwds).first()
        if o:
            return o
        else:
            return None

    @classmethod
    def create(cls, year_month, key, key_value='', num_datasets=0):
        '''
        Helper function to create an csc_published_dataset and save it.
        '''
        pd = cls(year_month=year_month, num_datasets=num_datasets)
        try:
            pd.save()
        except InvalidRequestError:
            model.Session.rollback()
            pd.save()
        finally:
            # No need to alert administrator so don't log as an error
            log_message = 'year_month {0}, num_datasets {1}'.format(year_month, num_datasets)
            log.debug(log_message)


csc_ga_dataset_table = Table(CSC_GA_DATASET_TABLE_NAME, metadata,
                          Column('year_month', types.UnicodeText, nullable = False),
                          Column('end_day', types.Integer, nullable = False),
                          Column('pageviews', types.Integer, nullable = False, server_default='0'),
                          Column('dataset_name', types.UnicodeText, nullable = False, server_default=u''),
                          PrimaryKeyConstraint('year_month', 'dataset_name'))
mapper(CscGaDataset, csc_ga_dataset_table)


csc_ga_session_table = Table(CSC_GA_SESSION_TABLE_NAME, metadata,
                          Column('year_month', types.UnicodeText, nullable = False),
                          Column('end_day', types.Integer, nullable = False),
                          Column('sessions', types.Integer, nullable = False, server_default='0'),
                          PrimaryKeyConstraint('year_month'))
mapper(CscGaSession, csc_ga_session_table)

csc_published_datasets_table = Table(CSC_PUBLISHED_DATASETS_TABLE_NAME, metadata,
        Column('year_month', types.UnicodeText, nullable=False),
        Column('num_datasets', types.Integer, server_default='0'),
        PrimaryKeyConstraint('year_month')
    )
mapper(CscPublishedDataset, csc_published_datasets_table,
    )


def init_tables():
    if (csc_ga_dataset_table not in metadata.sorted_tables and \
       csc_ga_session_table not in metadata.sorted_tables and \
       csc_published_datasets_table not in metadata.sorted_tables) or \
       (not csc_ga_dataset_table.exists(model.meta.engine) and \
        not csc_ga_session_table.exists(model.meta.engine) and \
        not csc_published_datasets_table.exists(model.meta.engine)):
        metadata.create_all(model.meta.engine)
        log.debug('All csc_report_tables created')
        print 'All csc_report_tables created'
    else:
        if not csc_ga_dataset_table.exists(model.meta.engine):
            csc_ga_dataset_table.create(model.meta.engine)
            log.debug('%s table created', CSC_GA_DATASET_TABLE_NAME)
            print '%s table created' % (CSC_GA_DATASET_TABLE_NAME)
        else:
            log.debug('%s table already exists', CSC_GA_DATASET_TABLE_NAME)
            print '%s table already exists' % (CSC_GA_DATASET_TABLE_NAME)

        if not csc_ga_session_table.exists(model.meta.engine):
            csc_ga_session_table.create(model.meta.engine)
            log.debug('%s table created', CSC_GA_SESSION_TABLE_NAME)
            print '%s table created' % (CSC_GA_SESSION_TABLE_NAME)
        else:
            log.debug('%s table already exists', CSC_GA_SESSION_TABLE_NAME)
            print '%s table already exists' % (CSC_GA_SESSION_TABLE_NAME)
        
        if not csc_published_datasets_table.exists(model.meta.engine):
            csc_published_datasets_table.create(model.meta.engine)
            log.debug('%s table created', CSC_PUBLISHED_DATASETS_TABLE_NAME)
            print '%s table created' % (CSC_PUBLISHED_DATASETS_TABLE_NAME)
        else:
            log.debug('%s table already exists', CSC_PUBLISHED_DATASETS_TABLE_NAME)
            print '%s table already exists' % (CSC_PUBLISHED_DATASETS_TABLE_NAME)

cached_tables = {}

def get_table(name):
    if name not in cached_tables:
        meta = MetaData()
        meta.reflect(bind=model.meta.engine)
        table = meta.tables[name]
        cached_tables[name] = table
    return cached_tables[name]

