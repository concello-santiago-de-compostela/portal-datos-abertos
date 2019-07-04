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

namespace Drupal\csc_menu_export\Form;

use Drupal\Core\Form\ConfigFormBase;
use Drupal\Core\Form\FormStateInterface;

class MenuExportConfigForm extends ConfigFormBase
{

    /**
     *
     * {@inheritdoc}
     * @see \Drupal\Core\Form\FormInterface::getFormId()
     */
    public function getFormId()
    {
        return 'menu_export_config_form';
    }

    /**
     *
     * {@inheritdoc}
     */
    protected function getEditableConfigNames()
    {
        return [
            'menuexport.config'
        ];
    }

    /**
     *
     * {@inheritdoc}
     * @see \Drupal\Core\Form\ConfigFormBase::buildForm()
     */
    public function buildForm(array $form, FormStateInterface $form_state)
    {
        $config = $this->config('menuexport.config');
        
        $form['export_directory'] = array(
            '#type' => 'textfield',
            '#title' => t("Export directory"),
            '#description' => t('Example: /sites/default/files'),
            '#default_value' => $config->get('export_directory')
        );
        
        $form['export_button'] = array(
            '#type' => 'submit',
            '#value' => t("Export"),
            '#submit' => array(
                'convertToJSON'
            ),
            '#validate' => array(
                'validateExport'
            )
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
        
        $this->config('menuexport.config')
            ->set('export_directory', $form_state->getValue('export_directory'))
            ->save();
    }

    public function validateForm(array &$form, FormStateInterface $form_state)
    {
        $path = $form_state->getValue('export_directory');
        
        if (! file_exists($path)) {
            $form_state->setErrorByName('export_directory', $this->t('The directory is not valid, please submit a valid one.'));
        }
    }
}