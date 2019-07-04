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
import csv
import json

from ckan.plugins.toolkit import url_for, response, config, BaseController
from ckan.plugins.toolkit import  render, _, asbool, NotAuthorized, abort
from ckanext.csc import helpers as ch
from datetime import datetime

log = logging.getLogger(__name__)

class CscController(BaseController):
    
    def dashboarddata(self):
        return render('dashboard/dashboard.html')

    def _write_error_csv(self, filename=datetime.now().strftime("%Y-%m-%d")):
        aux_filename = '%s.csv' % datetime.now().strftime("%Y-%m-%d")
        response.headers['Content-Type'] = "text/csv; charset=utf-8"
        response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename if filename else aux_filename))
        writer = csv.writer(response)
        writer.writerow([_('Error loading data')])

    def most_visited_datasets_csv(self):
        '''
        Returns a CSV with the most_visited_datasets.
        '''
        filename="most_visited_datasets_%s.csv" % datetime.now().strftime("%Y-%m-%d")
        try:
            json_result_data, json_month_name_list, month_name_list, json_column_titles, visible_visits = ch.csc_dashboard_data_most_visited_datasets(True)
            visible_visits = asbool(
                      config.get('ckanext.csc.dashboard.chart.most_visited_datasets.num_visits.visible', False))
            result_data = json.loads(json_result_data) if json_result_data else []
            response.headers['Content-Type'] = "text/csv; charset=utf-8"
            response.headers['Content-Disposition'] = str('attachment; filename=%s' % filename)
            column_titles = [_('Month').encode('utf-8'), _('Url').encode('utf-8'), _('Dataset').encode('utf-8'), _('Publisher').encode('utf-8')]
            if visible_visits:
                column_titles.append(_('Visits').encode('utf-8'))
            writer = csv.writer(response)
            writer.writerow(column_titles)
            prefix_url = config.get('ckan.site_url') + url_for(controller='package', action='search') + "/"
            for result in result_data:
                row = [
                        result.get('month', '').encode('utf-8'), 
                        prefix_url + result.get('url', ''),
                        result.get('title', '').encode('utf-8'),
                        result.get('publisher', '').encode('utf-8')
                      ]
                if visible_visits:
                    row.append(result.get('visits', 0))
                writer.writerow(row)
        except Exception as e:
            log.error('Exception in most_visited_datasets_csv: %s', e)
            self._write_error_csv(filename)
