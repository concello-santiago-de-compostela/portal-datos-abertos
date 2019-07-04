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

"use strict";

ckan.module('csc_dashboard_mostVisitedDatasets', function ($, _) {
  return {
    initialize: function () {
      var mvd_data_provider = this.options.data_provider;
      var mvd_filter_div = "#"+this.options.filter_divid;
      var mvd_filter_values = this.options.filter_values;
      jsGrid.locale(this.options.language);
      var mvd_grid = new jsGrid.Grid($("#" + this.options.divid), {
        fields: [
          { 
            name: "month_id", 
            type: "select", 
            width: 100, 
            items: mvd_filter_values, 
            valueField: "id",  
            textField: "name", 
            selectedIndex: 0, 
            filtering:true, 
            title: this.options.column_titles[0],
            valueType: "string",
            visible: false
          },
          { 
            name: "order", 
            type: "number", 
            width: "10%", 
            filtering:false, 
            align: "center", 
            title: this.options.column_titles[1]
          },
          { 
            name: "package", 
            type: "text", 
            width: "45%", 
            filtering:false, 
            title: this.options.column_titles[2]
          },
          { 
            name: "publisher", 
            type: "text", 
            width: this.options.visible_col_visits ? "30%" : "45%", 
            filtering:false, 
            title: this.options.column_titles[3]
          },
          { 
            name: "visits", 
            type: "number", 
            width: "15%", 
            filtering:false, 
            title: this.options.column_titles[4], 
            align: "center", 
            visible:this.options.visible_col_visits
          }
        ],
        data: mvd_data_provider, 
        width: "100%",
        height: "auto",
        filtering: false,
        selecting: false,
        sorting: true,
        autoload: true,
        noDataContent: this.options.no_data,
        controller: {
          loadData: function (filter) {
            var result = $.grep(mvd_data_provider, function(item, idx) {
              for (var key in filter) {
                var value = filter[key];
                if (value.length > 0) {
                  if (item[key].indexOf(value) == -1)
                    return false;
                }
              }
              return true;
            });
            return result;
          },
        }
      });
      $(mvd_filter_div).on("change", function(){
        var value = $(this).val();
        mvd_grid.loadData({'month_id': value});
      });
      mvd_grid.loadData({'month_id': mvd_filter_values[0]['id']});
    }
  }
});