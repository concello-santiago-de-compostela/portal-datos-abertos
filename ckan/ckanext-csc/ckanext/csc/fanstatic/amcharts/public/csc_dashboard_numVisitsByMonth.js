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

ckan.module('csc_dashboard_numVisitsByMonth', function ($, _) {
  return {
    initialize: function () {
      var chart_nvdgebm = AmCharts.makeChart(this.options.divid, {
        "type": "serial",
        "theme": "light",
        "language": this.options.language,
        "dataProvider": this.options.data_provider,
        "marginTop": 20,
        "marginBottom": 20,
        "marginRight": 70,
        "marginLeft": 70,
        "valueAxes": [{
          "axisAlpha": 0,
          "dashLength": 4,
          "position": "left"
        }],
        "numberFormatter": {
          "precision": -1,
          "decimalSeparator": (this.options.language == "en")?".":",",
          "thousandsSeparator": ""
        },
        "graphs": [{
          "id": "g1",
          "balloonText": "<div style='margin:10px; text-align:left;'><span style='font-size:13px'>[[category]]</span><br><span style='font-size:18px'>[[value]]</span>",
          "customBullet": "/catalogo/amcharts/data/images/star.png?x",
          "customBulletField": "customBullet",
          "bulletSize": 14,
          "lineThickness": 1,
          "negativeLineColor": "#637bb6",
          "valueField": "value",
          "connect": true,
        }],
        "titles": [
          {"text": this.options.title}
        ],
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
          "graphBulletSize": 1.5,
          "cursorAlpha": 0,
          "valueLineEnabled": true,
          "valueLineBalloonEnabled": true,
          "valueLineAlpha": 0.5,
          "fullWidth": true,
          "categoryBalloonDateFormat": (this.options.language == "en")?"YYYY MMM":"MMM YYYY"
        },
        "autoMargins": false,
        "dataDateFormat": "YYYY-MM",
        "categoryField": "date",
        "valueScrollbar": {
          "oppositeAxis": true,
          "offset": 30,
          "scrollbarHeight": 10
        },
        "categoryAxis": {
          "minPeriod": "MM",
          "parseDates": true,
          "equalSpacing": true,
          "axisAlpha": 0,
          "gridAlpha": 0,
          "inside": false,
          "tickLength": 0,
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
                var date = new Date(Date.parse(currentDataValue.date));
                date.setMonth(date.getMonth() + 1);
                date.setDate(0);
                var monthOffset = (date.getMonth()<9)?"0":"";
                currentDataValue.date = date.getFullYear()+"-"+monthOffset+(date.getMonth()+1)+"-"+date.getDate();
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