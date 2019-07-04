<?php
namespace Drupal\csc_ckan\Form;

use Drupal\Core\Form\ConfigFormBase;
use Drupal\Core\Form\FormStateInterface;

class ConfigForm extends ConfigFormBase
{

    /**
     *
     * {@inheritdoc}
     * @see \Drupal\Core\Form\FormInterface::getFormId()
     */
    public function getFormId()
    {
        return 'ckan_config_form';
    }

    /**
     *
     * {@inheritdoc}
     */
    protected function getEditableConfigNames()
    {
        return [
            'ckan.config'
        ];
    }

    /**
     * 
     * {@inheritDoc}
     * @see \Drupal\Core\Form\ConfigFormBase::buildForm()
     */
    public function buildForm(array $form, FormStateInterface $form_state)
    {
        $config = $this->config('ckan.config');
        
        $form['ckan_host'] = array(
            '#type' => 'textfield',
            '#title' => t("CKAN host"),
            '#description' => t('Example: http://172.22.194.80/api/3/'),
            '#default_value' => $config->get('ckan_host')
        );
        $form['ckan_api_key'] = array(
            '#type' => 'textfield',
            '#title' => t("CKAN API Key"),
            '#default_value' => $config->get('ckan_api_key')
        );
        $form['ckan_url'] = array(
            '#type' => 'textfield',
            '#title' => t("CKAN Public URL"),
            '#description' => t('Example: http://172.22.194.80'),
            '#default_value' => $config->get('ckan_url')
        );
        $form['ckan_pagina_dataset'] = array(
            '#type' => 'textfield',
            '#title' => t("CKAN dataset page"),
            '#description' => t('Example: dataset'),
            '#default_value' => $config->get('ckan_pagina_dataset')
        );
        
        return parent::buildForm($form, $form_state);
    }

    /**
     * 
     * {@inheritDoc}
     * @see \Drupal\Core\Form\ConfigFormBase::submitForm()
     */
    public function submitForm(array &$form, FormStateInterface $form_state)
    {
        parent::submitForm($form, $form_state);
        
        $this->config('ckan.config')
            ->set('ckan_host', $form_state->getValue('ckan_host'))
            ->set('ckan_api_key', $form_state->getValue('ckan_api_key'))
            ->set('ckan_url', $form_state->getValue('ckan_url'))
            ->set('ckan_pagina_dataset', $form_state->getValue('ckan_pagina_dataset'))
            ->save();
    }
}