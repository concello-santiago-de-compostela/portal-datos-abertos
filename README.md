# [Portal de Datos Abiertos de Santiago de Compostela](https://datos.santiagodecompostela.gal/)

Este repositorio contiene el código fuente del Portal de Datos Abiertos de Santiago de Compostela. Se proporcionan los componentes desarrollados para Drupal y para CKAN. Se puede consultar la arquitectura de alto nivel del proyecto en el [sitio web del proyecto Ciudades Abiertas](https://ciudadesabiertas.es/datos-abiertos/#Descripci%C3%B3n).

El Portal de Datos Abiertos de Santiago de Compostela forma parte de las actuaciones que se llevan a cabo dentro del proyecto ["Plataforma de Gobierno Abierto, Colaborativa e Interoperable"](https://ciudadesabiertas.es), presentado por los Ayuntamientos de [A Coruña](https://www.coruna.gal/), [Madrid](https://www.madrid.es/portal/site/munimadrid), [Santiago de Compostela](http://santiagodecompostela.gal/) y [Zaragoza](https://www.zaragoza.es/sedeelectronica/), que fue seleccionado como beneficiario de la ["II Convocatoria de Ciudades Inteligentes"](https://perfilcontratante.red.es/perfilcontratante/busqueda/DetalleLicitacionesDefault.action?idLicitacion=6707&visualizar=0) del [Ministerio de Economía y Empresa](http://www.mineco.gob.es/) lanzado a través de la [Entidad Pública Empresarial Red.es](https://www.red.es/redes/) adscrita a la [Secretaría de Estado de Avance Digital]((http://www.mineco.gob.es/portal/site/mineco/avancedigital)) de dicho Ministerio.


## CKAN

Se han desarrollado las siguientes extensiones de CKAN:

* ckanext-csc: contiene las adaptaciones específicas, tanto funcionales como de estilos.
* ckanext-csc_dcat: gestiona la exportación de los conjuntos de datos a DCAT para que sea compatible con la NTI.
* ckanext-csc-scheming: amplía el esquema de metadatos de CKAN a los requisitos de la [Norma Técnica de Interoperabilidad de Reutilización de recursos de la información (NTI-RISP)](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2013-2380).
* ckanext-csc-ga: integración con Google Analytics.
* ckanext-csc-reports: generación de información de reportes de Google Analytics.


### Dependencias

Requiere CKAN versión 2.8.2 y las siguientes extensiones:

* [ckanext-dcat](https://github.com/ckan/ckanext-dcat/releases/tag/v0.0.9)
* [ckanext-scheming](https://github.com/ckan/ckanext-scheming/tree/3bd3f0d25ce544144edd84ee9cb38addccbb6cfd)
* [ckanext-fluent] (https://github.com/ckan/ckanext-fluent/tree/07f061e0c98c53fffed8d1f7a1617e89d0b3a08d)
* [ckanext-disqus] (https://github.com/ckan/ckanext-disqus/tree/709566b439df6a9cf45708c773c18a71b141f3ef)
* [ckanext-spatial] (https://github.com/ckan/ckanext-spatial/tree/2acf66b110ba534750cab754a50566505ba88d83)

###  Instalación

El proceso de instalación de las extensiones sigue el mecanismo estándar de CKAN descrito en su [documentación oficial](http://docs.ckan.org/). Para cualquier consulta, puede utilizar el [punto de contacto](https://ciudadesabiertas.es/contacto/index.html) de Ciudades Abiertas.


## Drupal

Se incluyen en esta sección los módulos desarrollados para el proyecto, las features que deben ser activadas, el theme a integrar y el fichero composer en el que se basa el proyecto.

### Dependencias

Requiere Drupal versión 8.6.X y la siguiente librería no incluída en las dependencias de composer:

* [Colorbox plugin 1.x](https://github.com/jackmoore/colorbox/archive/1.x.zip)

### Instalación

El proceso de instalación debe seguir el modelo de despliegue de Drupal basado en [drupal-composer](https://github.com/drupal-composer/drupal-project) para poder descargar todas las dependencias del proyecto con la herramienta estándar de PHP Composer, incluido la versión del core de Drupal así como los módulos de terceros instalados con sus dependencias. En el proceso de instalación se debe realizar la activación de features, módulos e integración del theme. Se deben seguir las recomendaciones de la [documentación oficial de Drupal 8](https://www.drupal.org/docs/8). Para cualquier consulta, puede utilizar el [punto de contacto](https://ciudadesabiertas.es/contacto/index.html) de Ciudades Abiertas.

### Licencia

Los derechos de autor de esta aplicación pertenecen a © 2018 Ayuntamiento de Santiago de Compostela y Entidad Pública Empresarial Red.es. La licencia sobre el código fuente está cedida con arreglo a la [EUPL](https://eupl.eu/1.2/es/).
