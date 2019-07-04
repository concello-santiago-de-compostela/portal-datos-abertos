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

// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

$( document ).ready( function() {
    // Responsive main menu.
    $('#main-menu').smartmenus();

    // Main menu toggle.
    $('.navbar-toggle').click(function () {
      $('.region-primary-menu').slideToggle();
    });

    // Hide dropdown menu.
    if ($(window).width() < 768) {
      $('.region-primary-menu li a:not(.has-submenu)').click(function () {
        $('.region-primary-menu').hide();
      });
    }

    // Sliding header.
    $('.toggle-switch').click(function () {
      $('#sliding-header-wrap').slideToggle();
    });
  
    // Navbar feature
    var scrollTop = 0;
    jQuery(window).scroll(function(){
      scrollTop = jQuery(window).scrollTop();
      jQuery('.counter').html(scrollTop);
      if (scrollTop >= 125) {
        jQuery('.main-header').addClass('scrolled-nav');
      } else if (scrollTop < 100) {
        jQuery('.main-header').removeClass('scrolled-nav');
      }
    }); 
});