<?php
namespace Drupal\csc_ckan\Controller;

use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\Response;
use DgeCkanClient;

/**
 * Importación librería DGE_CKAN
 */
include_once (DRUPAL_ROOT . "/modules/custom/csc_ckan/libraries/dge_ckan_php_client/DgeCkanClient.php");

class CKANTestController extends ControllerBase
{

    /**
     * Test Page
     * 
     * @return string
     */
    function csc_ckan_page_test()
    {
        global $conf;
        
        $ckanConfig = \Drupal::config('ckan.config');
        
        $library = class_exists('DgeCkanClient');
        
        if (! $library) {
            drupal_set_message(t('DGE CKAN PHP Client is not installed'), 'error');
        }
        $apiUrl = $ckanConfig->get('ckan_host');
        $apiKey = $ckanConfig->get('ckan_api_key');
        $Ckan = new DgeCkanClient($apiUrl, $apiKey, $conf);
        
        $ckanResults = $Ckan->package_search('organization:irs-gov');
        
        $ckanResults = json_decode($ckanResults, true);
        $output = '';
        if ($ckanResults['success'] == 1) {
            drupal_set_message(t('CKAN Connexion is OK'));
            $output = t('RAW result') . ': ' . print_r($ckanResults, TRUE);
        } else {
            drupal_set_message(t('CKAN Connexion error'), 'error');
        }
        if (isset($conf['proxy_server']) && $conf['proxy_server'] != '') {
            $output .= '<br />' . t('Proxy server is configurated. IP !ip', array(
                '!ip' => $conf['proxy_server']
            ));
        }
        $response = $output . '<br />' . t('CKAN example connexion URL') . ': ' . print_r($Ckan->getCurlRequest(), TRUE);
       
        $build = [
            '#markup' => $response
        ];
        return $build;
    }
}