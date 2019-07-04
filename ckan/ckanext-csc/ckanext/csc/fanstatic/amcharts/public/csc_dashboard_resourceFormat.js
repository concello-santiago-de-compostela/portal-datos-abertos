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

ckan.module('csc_dashboard_resourceFormat', function ($, _) {
  return {
    initialize: function () {
      var chart_df = AmCharts.makeChart(this.options.divid, {
        "type": "pie",
        "startDuration": 0,
        "theme": "light",
        "language": this.options.language,
        "addClassNames": true,
        "marginTop": 0,
        "marginBottom": 0,
        "marginRight": 0,
        "marginLeft": 0,
        "maxLabelWidth": 110,
        "titles": [{
          "text": this.options.title, 
        }],
        "numberFormatter": {
          "precision": -1,
          "decimalSeparator": (this.options.language == "en")?".":",",
          "thousandsSeparator": ""
        },
        "balloonText": "[[title]]<br><span style='font-size:14px'><b>[[value]]</b> ([[percents]]%)</span>",
        "labelText": "[[title]]: [[value]] ([[percents]]%)",
        "innerRadius": "45%",
        "pullOutRadius": 20, 
        "allLabels": [{
          "y": "50%",
          "align": "center",
          "size": "50%",
          "bold": true,
          "text": ((this.options.data_text_1)?this.options.data_text_1:"") + 
                  ((this.options.data_text_2)?"\n" + this.options.data_text_2:""),
          "color": "#555"
        }],
        "defs": {
          "filter": [{
            "id": "shadow",
            "width": "200%",
            "height": "200%",
            "feOffset": {
              "result": "offOut",
              "in": "SourceAlpha",
              "dx": 0,
              "dy": 0
            },
            "feGaussianBlur": {
              "result": "blurOut",
              "in": "offOut",
              "stdDeviation": 5
            },
            "feBlend": {
              "in": "SourceGraphic",
              "in2": "blurOut",
              "mode": "normal"
            }
          }]
        },
        "dataProvider": this.options.data_provider,
        "groupedTitle": this.options.grouped_title,
        "groupPercent": this.options.group_percent,
        "valueField": "value",
        "titleField": "format",
        "export": {"enabled": true}, 
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
              if (this_chart.dataProvider == undefined || 
                  this_chart.dataProvider.length == 0) {
                this_chart.labelsEnabled = false;
                this_chart.addLabel("50%", "50%", e.chart.noDataLabel, "middle", 15);
                this_chart.alpha = 0.3;
              }
            }
          }
        ]
      });
      chart_df.addListener("rollOverSlice", function(e) {
        handleRollOver(e);
      });
      function handleRollOver(e) {
        var wedge = e.dataItem.wedge.node;
        wedge.parentNode.appendChild(wedge);
      }
    }
  };
});