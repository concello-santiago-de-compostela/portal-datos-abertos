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

ckan.module('csc_dropdown', function ($, _) {
  return {
    initialize: function () {
        console.log
      var $dropbutton = this;
      this.dropbutton = this.el;

      this.$list = this.el.find('.dropbutton');
      this.$actions = this.$list.find('li').addClass('dropbutton-action');
      
      //Set classes
      if (this.$actions.length > 1) {
        var $primary = this.$actions.slice(0, 1);
        var $secondary = this.$actions.slice(1);
        $secondary.addClass('secondary-action');

        $primary.after(this.dropbuttonToggle(this.options));

        this.dropbutton.addClass('dropbutton-multiple').on({
            'mouseleave.dropbutton': $.proxy(this.hoverOut, this),
            'mouseenter.dropbutton': $.proxy(this.hoverIn, this),
            'focusout.dropbutton': $.proxy(this.focusOut, this),
            'focusin.dropbutton': $.proxy(this.focusIn, this)
        });
      } else {
        this.dropbutton.addClass('dropbutton-single');
      }

      //Evento para abrir y cerrar
      this.el.on('click', '.dropbutton-toggle', this.dropbuttonClickHandler);
    },
    dropbuttonToggle: function(options){
       return '<li class="dropbutton-toggle"><button type="button"><span class="dropbutton-arrow"><span class="visually-hidden">' + options.title + '</span></span></button></li>';
    },
    dropbuttonClickHandler: function(e) {
        e.preventDefault();
        $(e.target).closest('.dropbutton-wrapper').toggleClass('open');
    },
    toggle: function toggle(show) {
        var isBool = typeof show === 'boolean';
        show = isBool ? show : !this.dropbutton.hasClass('open');
        this.dropbutton.toggleClass('open', show);
      },
    hoverIn: function hoverIn() {
        if (this.timerID) {
          window.clearTimeout(this.timerID);
        }
    },
    hoverOut: function hoverOut() {
        if (this.dropbutton.hasClass( "open" )) {
            var exthis = this;
            this.timerID = window.setTimeout(function () {exthis.close()}, 1000);
        }
    },
    open: function open() {
        this.toggle(true);
    },
    close: function close() {
        this.toggle(false);
    },
    focusOut: function focusOut(e) {
        this.hoverOut.call(this, e);
    },
    focusIn: function focusIn(e) {
        this.hoverIn.call(this, e);
    },
    dropbutton: null,
    timerID: 0
  };
});