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
 * Contains \Drupal\system\Plugin\Block\SocialSharingBlock.php
 */
namespace Drupal\csc_socialsharing\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Core\Form\FormStateInterface;

/**
 * Provides a '"CSC Social Sharing Block" block.
 *
 * @Block(
 * id = "csc_socialsharing_block",
 * admin_label = "CSC Social Sharing Block",
 * category = "Blocks"
 * )
 */
class SocialSharingBlock extends BlockBase
{

    public function build()
    {
        $config = \Drupal::config('socialsharing.config');
        
        $build = [];
        $pubid = $config->get('addthis_pubid');
        $build = [
            '#theme' => 'socialsharingblock_template',
            '#children' => '<!-- Go to www.addthis.com/dashboard to customize your tools -->
<script type="text/javascript" src="//s7.addthis.com/js/300/addthis_widget.js#pubid=' . $pubid . '">
</script>'
        ];
        
        return $build;
    }

    /**
     *
     * {@inheritdoc}
     * @see \Drupal\Core\Block\BlockBase::blockForm()
     */
    public function blockForm($form, FormStateInterface $form_state)
    {
        $form = parent::blockForm($form, $form_state);
        
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

    /**
     *
     * {@inheritdoc}
     * @see \Drupal\Core\Plugin\ContextAwarePluginBase::getCacheMaxAge()
     */
    public function getCacheMaxAge()
    {
        return 0;
    }
}