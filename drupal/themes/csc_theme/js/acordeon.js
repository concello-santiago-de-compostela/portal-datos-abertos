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

jQuery(document).ready(function() {
	jQuery(".acordeon__titulo").click(function() {

		var contenido = jQuery(this).next(".acordeon__contenido");

		if (contenido.css("display") == "none") { // open
			contenido.slideDown(250);
			jQuery(this).addClass("active");

		} else { // close

			contenido.slideUp(250);
			jQuery(this).removeClass("active");

		}

	});

	jQuery(".acordeon__titulo__categoria").click(function() {

		var contenido = jQuery(this).next(".acordeon__contenido__categoria");

		if (contenido.css("display") == "none") { // open

			contenido.slideDown(250);
			jQuery(this).addClass("active");

		} else { // close
			contenido.slideUp(250);
			jQuery(this).removeClass("active");

		}

	});
});