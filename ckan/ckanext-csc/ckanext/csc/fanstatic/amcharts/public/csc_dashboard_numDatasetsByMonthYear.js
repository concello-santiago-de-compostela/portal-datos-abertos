/**
 * Copyright 2018 Ayuntamiento de Santiago de Compostela, Entidad Pública Empresarial Red.es
 *
 * This file is part of the "Open Data Portal of Santiago de Compostela", developed within the "Ciudades Abiertas" project.
 *
 * Licensed under the EUPL, Version 1.2 or - as soon they will be approved by the European Commission - subsequent versions of the EUPL (the "Licence");
 * You may not use this work except in compliance with the Licence.
 * You may obtain a copy of the Licence at:
 *
 * https://joinup.ec.europa.eu/software/page/eupl
 *
 * Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the Licence for the specific language governing permissions and limitations under the Licence.
 */

// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

ckan.module('csc_dashboard_numDatasetsByMonthYear', function ($, _) {
  return {
    initialize: function () {
      var chart_ndpmy = AmCharts.makeChart(this.options.divid, {
        "type": "serial",
        "theme": "light",
        "language": this.options.language,
        "marginTop": 20,
        "marginBottom": 20,
        "marginRight": 70,
        "marginLeft": 70,
        "numberFormatter": {
          "precision": -1,
          "decimalSeparator": (this.options.language == "en")?".":",",
          "thousandsSeparator": ""
        },
        "dataProvider": this.options.data_provider,
        "valueAxes": [{
          "axisAlpha": 0,
          "position": "left"
        }],
        "graphs": [{
          "id": "g1",
          "balloonText": "[[category]]<br><b><span style='font-size:14px;'>[[value]]</span></b>",
          "bullet": "round",
          "bulletSize": 8,
          "lineColor": "#d1655d",
          "lineThickness": 2,
          "negativeLineColor": "#637bb6",
          "valueField": "value",
          "connect": true, 
        }],
        "titles": [],
        "chartScrollbar": {
          "graph": "g1",
          "gridAlpha": 0,
          "color": "#888888",
          "scrollbarHeight": 55,
          "backgroundAlpha": 0,
          "selectedBackgroundAlpha": 0.1,
          "selectedBackgroundColor": "#888888",
          "graphFillAlpha": 0,
          "autoGridCount": true,
          "selectedGraphFillAlpha": 0,
          "graphLineAlpha": 0.2,
          "graphLineColor": "#c2c2c2",
          "selectedGraphLineColor": "#888888",
          "selectedGraphLineAlpha": 1
        },
        "chartCursor": {
          "cursorAlpha": 0,
          "valueLineEnabled": true,
          "valueLineBalloonEnabled": true,
          "valueLineAlpha": 0.5,
          "fullWidth": true,
          "categoryBalloonDateFormat": (this.options.language == "en")?"YYYY MMM":"MMM YYYY"
        },
        "valueScrollbar": {
          "oppositeAxis": true,
          "offset": 30,
          "scrollbarHeight": 10
        },
        "dataDateFormat": "YYYY-MM",
        "categoryField": "year",
        "categoryAxis": {
          "minPeriod": "MM",
          "parseDates": true,
          "equalSpacing": false,
          "minorGridAlpha": 0.1,
          "minorGridEnabled": true,
          "startOnAxis": true,
          "dateFormats": [
            {period:'YYYY-MM',format:'MMM YY'},
            {period: 'MM',format: 'MMM YY'},
            {period: 'YYYY', format: 'MMM YY'}
          ]
        },
        "export": {
          "enabled": true,
          "processData": function(data, cfg) {
            //only for JSON and XLSX export.
            if ((cfg.format === "JSON" || cfg.format === "XLSX") && !cfg.ignoreThatRequest) {
              data.forEach(function(currentDataValue) {
                var date = new Date(Date.parse(currentDataValue.year));
                date.setMonth(date.getMonth() + 1);
                date.setDate(0);
                var monthOffset = (date.getMonth()<9)?"0":"";
                currentDataValue.year = date.getFullYear()+"-"+monthOffset+(date.getMonth()+1)+"-"+date.getDate();
              });
            }
            return data;
          }
        }, 
        "responsive": {"enabled": true},
        "noDataLabel": this.options.no_data,
        "listeners": [
          {
            "event": "init",
            "method": function(e) { 
              var this_chart = e.chart;
              if (this_chart.dataProvider == undefined || 
                  this_chart.dataProvider.length == 0) {
                this_chart.labelsEnabled = false;
                this_chart.addLabel("50%", "50%", e.chart.noDataLabel, "middle", 15);
                this_chart.alpha = 0.3;
              }
            }
          },
          {
            "event": "rendered",
            "method": function(e) { 
              var this_chart = e.chart;
              function zoomChart(){
                this_chart.zoomToIndexes(Math.round(this_chart.dataProvider.length * 0), Math.round(this_chart.dataProvider.length * 1));
              }
              if (this_chart.dataProvider == undefined || 
                  this_chart.dataProvider.length == 0) {
                this_chart.labelsEnabled = false;
                this_chart.addLabel("50%", "50%", e.chart.noDataLabel, "middle", 15);
                this_chart.alpha = 0.3;
              }
              zoomChart();
            }
          }
        ]
      });
    }
  };
});