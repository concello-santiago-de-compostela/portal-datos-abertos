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
namespace Drupal\csc_search\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Core\Form\FormStateInterface;

/**
 * Provides a '"CSC Search Block" block.
 *
 * @Block(
 * id = "csc_search_block",
 * admin_label = "CSC Search Block",
 * category = "Blocks"
 * )
 */
class CSCSearchBlock extends BlockBase
{

    /**
     *
     * {@inheritdoc}
     */
    public function build()
    {
        $form = \Drupal::formBuilder()->getForm(\Drupal\csc_search\Form\SearchForm::class);
        
        return $form;
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
        
        $form['ckan_url'] = array(
            '#type' => 'textfield',
            '#title' => t('CKAN Url'),
            '#default_value' => isset($config['ckan_url']) ? $config['ckan_url'] : ''
        );
        
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
        $values = $form_state->getValues();
        $this->configuration['ckan_url'] = $values['ckan_url'];
    }

    /**
     *
     * @param unknown $form
     * @param FormStateInterface $form_state
     */
    public function csc_search_submit($form, FormStateInterface &$form_state)
    {
        if (isset($this->configuration['ckan_url'])) {
            $form_state->setRedirect('route', $args, $options);
            $form_state->setRedirectUrl($this->configuration['ckan_url']);
        }
    }
}