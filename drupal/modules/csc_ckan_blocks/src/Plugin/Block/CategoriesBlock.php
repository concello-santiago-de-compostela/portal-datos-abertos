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
 * Contains \Drupal\system\Plugin\Block\CategoriesBlock.php
 */
namespace Drupal\csc_ckan_blocks\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Core\Form\FormStateInterface;


/**
 * Provides a '"CSC Datasets Categories Block" block.
 *
 * @Block(
 * id = "csc_categories_block",
 * admin_label = "CSC Categories Block",
 * category = "Blocks"
 * )
 */
class CategoriesBlock extends BlockBase{
    
    /**
     * 
     * {@inheritDoc}
     * @see \Drupal\Core\Block\BlockPluginInterface::build()
     */
    public function build()
    {
        $language = \Drupal::languageManager()->getCurrentLanguage()->getId();
        
        $categories_home = '';
        
        //Retrieve cached block
        if ($cached = \Drupal::cache()->get('csc_categories_home_'.$language))  {
           
            if ($cached->expire > time()) {
            
                $categories_home = $cached->data;
            }
        }
        if(empty($categories_home)) {
            //Call CKAN
            $categories_home = csc_ckan_blocks_categories_retrieve($language);
            //Cached every 6 hours by language
            \Drupal::cache()->set('csc_categories_home_'.$language, $categories_home, time() + 3600);
        }
        
        return array(
            '#categories' => $categories_home,
            '#theme' => 'categoriesblock_template',
            
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