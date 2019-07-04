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

namespace Drupal\csc_socialsharing\Form;

use Drupal\Core\Form\ConfigFormBase;
use Drupal\Core\Form\FormStateInterface;

class SocialSharingConfigForm extends ConfigFormBase
{

    /**
     *
     * {@inheritdoc}
     * @see \Drupal\Core\Form\FormInterface::getFormId()
     */
    public function getFormId()
    {
        return 'socialsharing_block_config_form';
    }

    /**
     *
     * {@inheritdoc}
     */
    protected function getEditableConfigNames()
    {
        return [
            'socialsharing.config'
        ];
    }

    /**
     *
     * {@inheritdoc}
     * @see \Drupal\Core\Form\ConfigFormBase::buildForm()
     */
    public function buildForm(array $form, FormStateInterface $form_state)
    {
        $config = $this->config('socialsharing.config');
        
        $form['addthis_pubid'] = array(
            '#type' => 'textfield',
            '#title' => t("AddThis Pubid"),
            '#description' => t('Example: ra-5bffae53928bca46'),
            '#default_value' => $config->get('addthis_pubid')
        );
        
        return parent::buildForm($form, $form_state);
    }

    /**
     *
     * {@inheritdoc}
     * @see \Drupal\Core\Form\ConfigFormBase::submitForm()
     */
    public function submitForm(array &$form, FormStateInterface $form_state)
    {
        parent::submitForm($form, $form_state);
        $config = $this->config('socialsharing.config');
        
        $values = $form_state->getValues();
        
        $config->set('addthis_pubid', $values['addthis_pubid'])->save();
    }
}