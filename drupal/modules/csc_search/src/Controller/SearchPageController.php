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

namespace Drupal\csc_search\Controller;

use Drupal\Core\Controller\ControllerBase;

class SearchPageController extends ControllerBase
{

    /**
     * Provides data for CSC Complex Block
     *
     * @return renderable array
     */
    public function content()
    {
        $keywords = \Drupal::request()->get('keywords');
        
        $language = \Drupal::languageManager()->getCurrentLanguage()->getId();
        $langParams = [];
        array_push($langParams, $language);
        
        $build = [];
        
        $settings = array(
            'rows' => 3,
            'start' => 0,
            'sort' => 'metadata_created desc'
        );
        
        $index = \Drupal\search_api\Entity\Index::load('default_solr_index');
        $query = $index->query();
        
        // Change the parse mode for the search.
        $parse_mode = \Drupal::service('plugin.manager.search_api.parse_mode')->createInstance('direct');
        $parse_mode->setConjunction('OR');
        $query->setParseMode($parse_mode);
        
        $query->addCondition('status', 1);
        
        // Set fulltext search keywords and fields.
        $query->keys($keywords);
        
        $query->sort('created', 'DESC');
        
        $query->setLanguages($langParams);
        
        // Do paging.
        $query->range(0, 3);
        
        // Set one or more tags for the query.
        // @see hook_search_api_query_TAG_alter()
        // @see hook_search_api_results_TAG_alter()
        $query->addTag('custom_search');
        
        // Execute the search.
        $results = $query->execute();
        
        $drupalItems = [];
        foreach ($results->getResultItems() as $item) {
            $nid = filter_var($item->getId(), FILTER_SANITIZE_NUMBER_INT);
            $entity = node_load($nid);
            if ($entity->getType() == 'preguntas_frecuentes') { // El campo descripción de FAQ no es el de "body" por defecto
                
                if (empty($entity->getTranslation($language)->get('field_descripcion')->summary)) {
                    $description = substr(strip_tags($entity->getTranslation($language)->get('field_descripcion')->value), 0, strrpos(substr(strip_tags($entity->getTranslation($language)->get('field_descripcion')->value), 0, 200), ' ')) . "...";
                } else {
                    $description = substr(strip_tags($entity->getTranslation($language)->get('field_descripcion')->summary), 0, strrpos(substr(strip_tags($entity->getTranslation($language)->get('field_descripcion')->summary), 0, 200), ' ')) . "...";
                }
                
                array_push($drupalItems, array(
                    'title' => $entity->getTranslation($language)->get('title')->value,
                    'description' => $description,
                    'type' => $entity->getTranslation($language)->getType(),
                    'url' => $entity->getTranslation($language)
                        ->toUrl()
                        ->toString()
                ));
            } else {
                
                if (empty($entity->getTranslation($language)->get('body')->summary)) {
                    $description = substr(strip_tags($entity->getTranslation($language)->get('body')->value), 0, strrpos(substr(strip_tags($entity->getTranslation($language)->get('body')->value), 0, 200), ' ')) . "...";
                } else {
                    $description = substr(strip_tags($entity->getTranslation($language)->get('body')->summary), 0, strrpos(substr(strip_tags($entity->getTranslation($language)->get('body')->summary), 0, 200), ' ')) . "...";
                }
                
                array_push($drupalItems, array(
                    'title' => $entity->getTranslation($language)->get('title')->value,
                    'description' => $description,
                    'type' => $entity->getTranslation($language)->type->entity->label(),
                    'url' => $entity->getTranslation($language)
                        ->toUrl()
                        ->toString()
                ));
            }
        }
        $block = \Drupal\block\Entity\Block::load('csccomplexsearchblock');
        if ($block) {
            $blocksettings = $block->get('settings');
            $ckanUrl = $blocksettings['ckan_url'];
        }
        
        global $base_url;
        $ckanUrl = $base_url . $ckanUrl . "/" . $language . '/dataset?q=' . $keywords;
        
        $solrUrl = $base_url . "/" . $language . "/buscador?search_api_fulltext=" . $keywords;
        $build = [
            '#keywordtext' => t('Results for the text ') . '"' . $keywords . '"',
            '#packages' => csc_ckan_blocks_package_search($keywords, '', $settings['rows'], $settings['start'], $settings['sort']),
            '#contents' => $drupalItems,
            '#ckan_url' => $ckanUrl,
            '#solr_url' => $solrUrl,
            '#language' => $language,
            '#theme' => 'complexsearch_template'
        ];
        
        return $build;
    }
}