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

/**
 * @file
 * Contains \Drupal\system\Plugin\Block\DatasetsNumberBlock.php
 */
namespace Drupal\csc_ckan_blocks\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Core\Form\FormStateInterface;

/**
 * Provides a '"CSC Datasets Number Block" block.
 *
 * @Block(
 * id = "csc_datasets_number_block",
 * admin_label = "CSC Datasets Number Block",
 * category = "Blocks"
 * )
 */
class DatasetsNumberBlock extends BlockBase
{

    /**
     *
     * {@inheritdoc}
     * @see \Drupal\Core\Block\BlockPluginInterface::build()
     */
    public function build()
    {
        $ckanConfig = \Drupal::config('ckan.config');
        $language = \Drupal::languageManager()->getCurrentLanguage()->getId();
        
        $settings = array(
            'rows' => 0,
            'start' => 0,
            'sort' => 'metadata_created desc'
        );
        
        //DRUPAL - Caché.
        /*drupal_flush_all_caches();
        \Drupal::service('page_cache_kill_switch')->trigger();*/
        
        $ckan = csc_ckan_init_class();
                
        $response = $ckan->request('package_search', '', '', $settings['rows'], $settings['start'], $settings['sort']);
        $packagesNumber = $response['result']['count'];
       

        return array(
            '#packagesnumber' => $packagesNumber,
            '#theme' => 'packagesnumberblock_template'
        
        );
    }

    /**
     *
     * {@inheritdoc}
     * @see \Drupal\Core\Block\BlockBase::blockForm()
     */
    public function blockForm($form, FormStateInterface $form_state)
    {
        $form = parent::blockForm($form, $form_state);
        
        $config = $this->getConfiguration();
        
        return $form;
    }

    /**
     *
     * {@inheritdoc}
     * @see \Drupal\Core\Block\BlockBase::blockSubmit()
     */
    public function blockSubmit($form, FormStateInterface $form_state)
    {
        parent::blockSubmit($form, $form_state);
    }
}

    
    
    
    
    
