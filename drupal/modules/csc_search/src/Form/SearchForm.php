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

namespace Drupal\csc_search\Form;

use Drupal\Core\Form\FormBase;
use Drupal\Core\Form\FormStateInterface;
use Drupal\Core\Routing\TrustedRedirectResponse;

class SearchForm extends FormBase
{

    /**
     *
     * {@inheritdoc}
     */
    public function getFormId()
    {
        return 'csc_search_form_custom';
    }

    /**
     *
     * {@inheritdoc}
     * @see \Drupal\Core\Form\FormInterface::buildForm()
     */
    public function buildForm(array $form, FormStateInterface $form_state)
    {
        $form['search_box'] = array(
            '#type' => 'textfield',
            '#title' => t('Search'),
            '#prefix' => '<div id="campo-text">',
            '#title_display' => 'invisible',
            '#placeholder' => t('What are you looking for?'),
            '#default_value' => '',
            '#suffix' => '</div>'
        );
        $form['search_submit'] = array(
            '#type' => 'submit',
            '#value' => t('Search'),
            '#prefix' => '<div id="campo-submit">',
            '#suffix' => '</div>',
            '#submit[]' => array(
                'csc_search_submit'
            )
        );
        
        return $form;
    }

    /**
     * 
     * {@inheritDoc}
     * @see \Drupal\Core\Form\FormBase::validateForm()
     */
    public function validateForm(array &$form, FormStateInterface $form_state) {
       
        $block = \Drupal\block\Entity\Block::load('cscsearchblock');
        
        if ($block) {
            
            $settings = $block->get('settings');
            $ckanUrl = $settings['ckan_url'];
        }
       
        if (empty($ckanUrl)) {
            $form_state->setErrorByName('search_box', t('The search url has not been configured'));
        }
    }
    
    
    /**
     *
     * {@inheritdoc}
     * @see \Drupal\Core\Form\FormInterface::submitForm()
     */
    public function submitForm(array &$form, FormStateInterface $form_state)
    {
        $language = \Drupal::languageManager()->getCurrentLanguage()->getId();
       
        
        $block = \Drupal\block\Entity\Block::load('cscsearchblock');
        
        if ($block) {
            
            $settings = $block->get('settings');
            $ckanUrl = $settings['ckan_url'];
        }
        
        global $base_url;
        
        $response = new TrustedRedirectResponse($base_url . "/" . $ckanUrl . "/" . $language . '/dataset?q=' . trim($form_state->getValue([
            'search_box'
        ])));
        
        $form_state->setResponse($response);
    }
}
