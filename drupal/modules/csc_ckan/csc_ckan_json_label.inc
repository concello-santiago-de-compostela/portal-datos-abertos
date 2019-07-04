<?php

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


class csc_ckan_json_label {
    var $file_name;
    var $json_data;
    function csc_ckan_json_label($file_name) {
        $this->file_name = $file_name;
        $this->json_data = $this->read_json();
    }
    function read_json()
    {
        $path = drupal_get_path('module', 'csc_ckan') . '/json/' . $this->file_name;
        $data = file_get_contents($path);
        $json_data = json_decode($data,true);
        return $json_data;
    }
}