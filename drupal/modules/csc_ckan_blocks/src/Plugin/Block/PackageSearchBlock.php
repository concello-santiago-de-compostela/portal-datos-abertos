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
 * Contains \Drupal\system\Plugin\Block\CSCSearchBlock.php
 */
namespace Drupal\csc_ckan_blocks\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Core\Form\FormStateInterface;

/**
 * Provides a '"CSC Package Search Block" block.
 *
 * @Block(
 * id = "csc_package_search_block",
 * admin_label = "CSC Package Search Block",
 * category = "Blocks"
 * )
 */
class PackageSearchBlock extends BlockBase
{
    
    /**
     * 
     * {@inheritDoc}
     * @see \Drupal\Core\Block\BlockPluginInterface::build()
     */
    public function build()
    {
        $ckanConfig = \Drupal::config('ckan.config');
        $language = \Drupal::languageManager()->getCurrentLanguage()->getId();
        
        $build = [];
        
        $settings = array(
            'rows' => 6,
            'start' => 0,
            'sort' => 'modified_date desc',
        );
        
        return array(
            '#packages' => csc_ckan_blocks_package_search('','',$settings['rows'],$settings['start'],$settings['sort']),
            '#ckan_url' => $ckanConfig->get('ckan_url').'/'.$language.'/'.$ckanConfig->get('ckan_pagina_dataset'),
            '#theme' => 'searchblock_template',
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
