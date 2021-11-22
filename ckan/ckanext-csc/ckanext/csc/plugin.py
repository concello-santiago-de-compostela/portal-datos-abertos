#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2018 Ayuntamiento de Santiago de Compostela, Entidad Pública Empresarial Red.es
# 
# This file is part of the "Open Data Portal of Santiago de Compostela", developed within the "Ciudades Abiertas" project.
# 
# Licensed under the EUPL, Version 1.2 or - as soon they will be approved by the European Commission - subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
# 
# https://joinup.ec.europa.eu/software/page/eupl
# 
# Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the Licence for the specific language governing permissions and limitations under the Licence.
 
from ckan import plugins
from ckan.plugins import toolkit, IBlueprint
from ckan.lib.plugins import DefaultTranslation
from ckanext.scheming import helpers as sh
from routes.mapper import SubMapper, Mapper as _Mapper
from ckan.common import g
from ckan.lib import mailer
from ckan.lib import helpers as ckan_helpers
from ckan.lib import i18n as i18n
from ckan import logic as logic
from ckan import model as model
from ckan.lib.navl import dictization_functions
from ckan.logic import auth as logic_auth
from ckan.logic import action as logic_action
from ckan import authz as authz
from flask import Blueprint
from six import text_type
from ckan.views.user import PerformResetView, RequestResetView

from ckan.exceptions import CkanUrlException

from ckanext.csc import helpers
from ckan.plugins.toolkit import url_for, redirect_to, request, config, render
from ckan.plugins.toolkit import get_action, check_access, _, abort, NotAuthorized

import logging
import json
import re

log = logging.getLogger(__name__)

def csc_auth_package_activity_list_html(context, data_dict):
    user = context.get('user')
    package = logic_auth.get_package_object(context, data_dict)
    authorized = False
    if package.owner_org:
        authorized = authz.has_user_permission_for_group_or_org(
            package.owner_org, user, 'update_dataset' )
    if not authorized:
        return {'success': False,
                'msg': _('Unauthorized to see this content')}
    return {'success': True}


def csc_auth_group_activity_list_html(context, data_dict):
    user = context.get('user')
    group = logic_auth.get_group_object(context, data_dict)
    authorized = authz.has_user_permission_for_group_or_org(group.id,
                                                                user,
                                                                'update')
    if not authorized:
        return {'success': False,
                'msg': _('Unauthorized to see this content')}
    return {'success': True}


def csc_auth_organization_activity_list_html(context, data_dict):
    user = context.get('user')
    organization = logic_auth.get_group_object(context, data_dict)
    authorized = authz.has_user_permission_for_group_or_org(organization.id,
                                                                user,
                                                                'update')
    if not authorized:
        return {'success': False,
                'msg': _('Unauthorized to see this content')}
    return {'success': True}

@toolkit.auth_disallow_anonymous_access
def csc_action_package_activity_list_html(context, data_dict):
    '''Return a package's activity stream.
       You must be authorized to edit the package.
    '''
    try:
        check_access('csc_package_activity_list_html', context, data_dict)
        return logic_action.get.package_activity_list_html(context, data_dict)
    except NotAuthorized:
        abort(403, _('Unauthorized to see this content') )


@toolkit.auth_disallow_anonymous_access
def csc_action_group_activity_list_html(context, data_dict):
    '''Return a group's activity stream.
       You must be authorized to edit the grup.
    '''
    try:
        check_access('csc_group_activity_list_html', context, data_dict)
        return logic_action.get.group_activity_list_html(context, data_dict)
    except NotAuthorized:
        abort(403, _('Unauthorized to see this content') )


@toolkit.auth_disallow_anonymous_access
def csc_action_organization_activity_list_html(context, data_dict):
    '''Return an organization's activity stream.
       You must be authorized to edit the organization.
    '''
    try:
        check_access('csc_organization_activity_list_html', context, data_dict)
        return logic_action.get.organization_activity_list_html(context, data_dict)
    except NotAuthorized:
        abort(403, _('Unauthorized to see this content') )


def csc_followers(id):
    abort(404, _(u'Resource not found'))


class CscRequestResetView(RequestResetView):
    def _prepare(self):
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'auth_user_obj': g.userobj
        }
        try:
            logic.check_access(u'request_reset', context)
        except logic.NotAuthorized:
            abort(403, _(u'Unauthorized to request reset password.'))

    def post(self):
        self._prepare()
        id = request.form.get(u'user')
        if id in (None, u''):
            ckan_helpers.flash_error(_(u'Email is required'))
            return ckan_helpers.redirect_to(u'/user/reset')
        log.info(u'Password reset requested for user "{}"'.format(id))

        context = {u'model': model, u'user': g.user, u'ignore_auth': True}
        user_objs = []

        # Usernames cannot contain '@' symbols
        if u'@' in id:
            # Search by email address
            # (You can forget a user id, but you don't tend to forget your
            # email)
            user_list = logic.get_action(u'user_list')(context, {
                u'email': id
            })
            if user_list:
                # send reset emails for *all* user accounts with this email
                # (otherwise we'd have to silently fail - we can't tell the
                # user, as that would reveal the existence of accounts with
                # this email address)
                for user_dict in user_list:
                    # This is ugly, but we need the user object for the mailer,
                    # and user_list does not return them
                    logic.get_action(u'user_show')(
                        context, {u'id': user_dict[u'id']})
                    user_objs.append(context[u'user_obj'])

        else:
            # Search by user name
            # (this is helpful as an option for a user who has multiple
            # accounts with the same email address and they want to be
            # specific)
            try:
                logic.get_action(u'user_show')(context, {u'id': id})
                user_objs.append(context[u'user_obj'])
            except logic.NotFound:
                pass

        if not user_objs:
            log.info(u'User requested reset link for unknown user: {}'
                     .format(id))

        for user_obj in user_objs:
            log.info(u'Emailing reset link to user: {}'
                     .format(user_obj.name))
            try:
                # FIXME: How about passing user.id instead? Mailer already
                # uses model and it allow to simplify code above
                mailer.send_reset_link(user_obj)
            except mailer.MailerException as e:
                # SMTP is not configured correctly or the server is
                # temporarily unavailable
                log.info("************* EXCEPTION******")
                ckan_helpers.flash_error(_(u'Error sending the email. Try again later '
                                'or contact an administrator for help'))
                log.exception(e)
                return ckan_helpers.redirect_to(ckan_helpers.url_for('/'))

        # always tell the user it succeeded, because otherwise we reveal
        # which accounts exist or not
        ckan_helpers.flash_success(
            _(u'A reset link has been emailed to you '
              '(unless the account specified does not exist)'))
        return ckan_helpers.redirect_to(ckan_helpers.url_for('/'))

    def get(self):
        self._prepare()
        return render(u'user/request_reset.html', {})

class CscPerformResetView(PerformResetView):

    def post(self, id):
        context, user_dict = super(CscPerformResetView, self)._prepare(id)
        context[u'reset_password'] = True
        user_state = user_dict[u'state']
        try:
            new_password = super(CscPerformResetView, self)._get_form_password()
            user_dict[u'password'] = new_password
            username = request.form.get(u'name')
            if (username is not None and username != u''):
                user_dict[u'name'] = username
            user_dict[u'reset_key'] = g.reset_key
            user_dict[u'state'] = model.State.ACTIVE
            get_action(u'user_update')(context, user_dict)
            mailer.create_reset_key(context[u'user_obj'])
            ckan_helpers.flash_success(_(u'Your password has been reset.'))
            return ckan_helpers.redirect_to(ckan_helpers.url_for('/'))
        except logic.NotAuthorized:
            log.error('NotAuthorized')
            ckan_helpers.flash_error(_(u'Unauthorized to edit user %s') % id)
        except logic.NotFound:
            ckan_helpers.flash_error(_(u'User not found'))
        except dictization_functions.DataError:
            ckan_helpers.flash_error(_(u'Integrity Error'))
        except logic.ValidationError as e:
            ckan_helpers.flash_error(u'%r' % e.error_dict)
        except ValueError as e:
            ckan_helpers.flash_error(text_type(e))
        user_dict[u'state'] = user_state
        return render(u'user/perform_reset.html', {
            u'user_dict': user_dict
        })

    def get(self, id):
        return super(CscPerformResetView, self).get(id)


class CscPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.ITranslation, inherit=True)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IAuthFunctions, inherit=True)
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.IBlueprint, inherit=True)

    # ###############################################
    # IConfigurer
    # ###############################################

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'csc')

        # patch helpers.py build url
        ckan_helpers._local_url = csc_local_url
    


    # ###############################################
    # ITemplateHelpers
    # ###############################################
    def get_helpers(self):
        return {
            'csc_default_locale': helpers.csc_default_locale,
            'csc_exported_catalog_files': helpers.csc_exported_catalog_files,
            'csc_theme_id': helpers.csc_theme_id,
            'csc_dataset_display_frequency': helpers.csc_dataset_display_frequency,
            'csc_list_themes': helpers.csc_list_themes,
            'csc_dataset_field_value': helpers.csc_dataset_field_value,
            'csc_resource_display_name_or_desc': helpers.csc_resource_display_name_or_desc,
            'csc_render_datetime': helpers.csc_render_datetime,
            'csc_dataset_display_name': helpers.csc_dataset_display_name,
            'csc_resource_display_name': helpers.csc_resource_display_name,
            'csc_get_portal_name': helpers.csc_get_portal_name,
            'csc_dataset_tag_list_display_names': helpers.csc_dataset_tag_list_display_names,
            'csc_dataset_display_fields': helpers.csc_dataset_display_fields,
            'csc_sort_alphabetically_resources': helpers.csc_sort_alphabetically_resources,
            'csc_get_addthis_route': helpers.csc_get_addthis_route,
            'csc_list_reduce_resource_format_label': helpers.csc_list_reduce_resource_format_label,
            'csc_resource_format_label': helpers.csc_resource_format_label,
            'csc_get_cookieconsent_link': helpers.csc_get_cookieconsent_link,
            'csc_main_menu_items': helpers.csc_main_menu_items,
            'csc_footer_menu_items': helpers.csc_footer_menu_items,
            'csc_dashboard_data_num_datasets_by_month_year': helpers.csc_dashboard_data_num_datasets_by_month_year,
            'csc_dashboard_data_resource_format': helpers.csc_dashboard_data_resource_format,
            'csc_dashboard_data_num_datasets_by_category': helpers.csc_dashboard_data_num_datasets_by_category,
            'csc_dashboard_data_num_visits': helpers.csc_dashboard_data_num_visits,
            'csc_dashboard_data_most_visited_datasets': helpers.csc_dashboard_data_most_visited_datasets,
            'csc_get_visibility_of_public_graphs': helpers.csc_get_visibility_of_public_graphs,
            'csc_show_english_values': helpers.csc_show_english_values,
            #'url_for' : helpers.csc_url_for,
            #'url_for_static_or_external': helpers.ckan_url_for_static_or_external,
            }

    
    
    # ###############################################
    # IFacets
    # ###############################################
    
    #Remove group facet
    def _del_facets(self, facets_dict):
        if 'group' in facets_dict:
           del facets_dict['group']
        return facets_dict
    
    def _add_csc_facets(self, facets_dict):
        facets_dict.clear()
        facets_dict['theme_id'] = toolkit._('Category')
        facets_dict['res_format_label'] = toolkit._('Format')
        facets_dict['organization'] = toolkit._('Publisher')
        facets_dict['frequency_id'] = toolkit._('Update frequency')
        facets_dict['tags'] = toolkit._('Tag')
        return facets_dict
    
    def dataset_facets(self, facets_dict, package_type):
        return self._add_csc_facets(facets_dict)
    
    def group_facets(self, facets_dict, group_type, package_type):
        return self._add_csc_facets(facets_dict)

    def organization_facets(self, facets_dict, organization_type, package_type):
        facets = self._add_csc_facets(facets_dict)
        if 'organization' in facets_dict: 
            del facets_dict['organization']
        return facets_dict
            

    
    # ###############################################
    # IFacets
    # ###############################################
    
    def before_index(self, data_dict):
        dataset = sh.scheming_get_schema('dataset', 'dataset')
        if ('res_format' in data_dict):
            #Get format field
            formats = sh.scheming_field_by_name(dataset.get('resource_fields'),
                            'format')
 
            #Create SOLR field
            data_dict['res_format_label'] = []
            for res_format in data_dict['res_format']:
                #Get format label
                res_format_label = sh.scheming_choices_label(formats['choices'], res_format)
                if res_format_label:
                    #Add label to new SOLR field
                    data_dict['res_format_label'].append(res_format_label)
 
        if ('frequency' in data_dict):
            #Get frequency field
            frequency = data_dict['frequency']
            if frequency:
                freq = json.loads(frequency)
                ftype = freq['type']
                fvalue = freq['value']
                data_dict['frequency_id']='{value}-{type}'.format(type=ftype, value=fvalue)
                data_dict['frequency_label']= helpers.csc_dataset_display_frequency(fvalue, ftype)
                #log.info('Frecuency = {f1}, frequency_id={f2}, frequency_label={f3}'.format(f1=frequency, f2=data_dict['frequency_id'], f3=data_dict['frequency_label']))
                       
 
        if ('theme' in data_dict):
            #Get theme field
            categoria = sh.scheming_field_by_name(dataset.get('dataset_fields'),
                            'theme')
 
            #Get theme value
            valor_categoria = data_dict['theme']
 
            #Empty theme values
            data_dict['theme'] = []
            data_dict['theme_id'] = []
            data_dict['theme_es'] = []
            data_dict['theme_gl'] = []
 
            #Get key values
            valores = valor_categoria.replace('[','').replace(']','')
            categorias = valores.split('", "')
            #Get translated label for each key
            for term_categoria in list(categorias):
                clean_term = term_categoria.replace('"','')
                data_dict['theme'].append(clean_term)
                data_dict['theme_id'].append(helpers.csc_theme_id(clean_term))
                #Look for label in the scheme
                for option in categoria.get('choices'):
                    if option['value'] == clean_term:
                        #Add label for each language
                        data_dict['theme_es'].append(option['label']['es'])
                        data_dict['theme_gl'].append(option['label']['gl'])
        return data_dict
    

    def before_search(self, search_params):        
        order_by = search_params.get('sort', '')
        if not order_by:
            search_params['sort'] = 'metadata_modified desc'
        return search_params


    def after_search(self, search_results, search_params):
       
        # Translate the unselected search facets.
        facets = search_results.get('search_facets')
        if not facets:
            return search_results

        desired_lang_code = request.environ.get('CKAN_LANG')
        fallback_lang_code = config.get('ckan.locale_default', 'es')

        # Look up translations for all of the facets in one db query.
        dataset = sh.scheming_get_schema('dataset', 'dataset')
        categoria = sh.scheming_field_by_name(dataset.get('dataset_fields'), 'theme')
        dict_categoria = {}
        for option in categoria.get('choices'):
            label_option = (option.get('label')).get(desired_lang_code, None)
            if not label_option:
                 label_option = (option.get('label')).get(fallback_lang_code, None)
            dict_categoria[helpers.csc_theme_id(option.get('value'))] = label_option
        facet = facets.get('theme_id', None)
        if facet:
            for item in facet.get('items', None):
                item['display_name'] = dict_categoria.get(item.get('name'), item.get('display_name'))
                item['class'] = item.get('name')
        
        facet = facets.get('frequency_id', None)
        if facet:
            for item in facet.get('items', None):
                #log.info("facet {facet}".format(facet=facet))
                value = item.get('name', '').split('-')
                item['display_name'] = helpers.csc_dataset_display_frequency(value[0], value[1])
        return search_results
    

    # ###############################################
    # IRoutes
    # ###############################################
    def before_map(self, _map):
        try:
            #log.debug("before_map")

            with SubMapper(_map, controller='ckanext.csc.controllers:CscController') as m:
                m.connect('dashboarddata', '/dashboarddata', action='dashboarddata')
                m.connect('most_visited_datasets_csv', '/csv-download/most-visited-datasets', action='most_visited_datasets_csv')

           
           
            with SubMapper(_map, controller='error') as m:
                m.connect('group_about', '/group/about/{id}', action='about',
                  ckan_icon='info-circle')
                m.connect('group_followers', '/group/followers/{id}', action='followers')
                m.connect('group_follow', '/group/follow/{id}', action='follow')
                m.connect('group_unfollow', '/group/unfollow/{id}', action='unfollow')
    
            with SubMapper(_map, controller='error') as m:
                m.connect('organization_about', '/organization/about/{id}',
                  action='about', ckan_icon='info-circle')

            with SubMapper(_map, controller='error') as m:
                m.connect('dataset_followers', '/dataset/followers/{id}', action='followers')
                m.connect('dataset_follow', '/dataset/follow/{id}', action='follow')
                m.connect('dataset_unfollow', '/dataset/unfollow/{id}', action='unfollow')
            
            with SubMapper(_map, controller='error') as m:
                m.connect('stats', '/stats', action='index')
                m.connect('stats_action', '/stats/{action}')

            #other hidding pages
            _map.redirect('/', '/dataset')
            
            
           
        except Exception as e:
            log.warn("MAP Before_map exception %r: %r:", type(e), e.message)
        #log.warning("CSC-map=%r", _map.__str__())
        return _map

    def after_map(self, _map):

        """log.warning("CSC CKAN map=%r**************", map.__str__())
        log.warning("INIT ALL CKAN ROUTING")
        def format_methods(r):
            if r.conditions:
                method = r.conditions.get('method', '')
                return type(method) is str and method or ', '.join(method)
            else:
                return ''
               
        table = [('Route name', 'Methods', 'Path', 'Controller', 'action')] + \
                [(r.name or '', format_methods(r), r.routepath or '',
                r.defaults.get('controller', ''), r.defaults.get('action', ''))
                for r in _map.matchlist]
              
        widths = [max(len(row[col]) for row in table)
                for col in range(len(table[0]))]
              
        print '\n'.join(
                ' '.join(row[col].ljust(widths[col])
                for col in range(len(widths)))
                for row in table)
                   
        log.warning("END ALL CKAN ROUTING") """
        return _map

    # ###############################################
    # IActions
    # ###############################################
    def get_actions(self):
        return {
            'package_activity_list_html' : csc_action_package_activity_list_html,
            'group_activity_list_html' : csc_action_group_activity_list_html,
            'organization_activity_list_html' : csc_action_organization_activity_list_html,
        }
        
    # ###############################################
    # IBlueprint
    # ###############################################

    def get_blueprint(self):
        '''Return a Flask Blueprint object to be registered by the app.'''

        # Create Blueprint for plugin
        blueprint = Blueprint(self.name, self.__module__)
        blueprint.template_folder = u'templates'
        # Add plugin url rules to Blueprint object
        rules = [
            (u'/user/followers/<id>', u'user_followers', csc_followers),
            (u'/user/reset', u'user_request_reset', CscRequestResetView.as_view(str(u'csc_request_reset'))),
            (u'/user/reset/<id>', u'user_perform_reset', CscPerformResetView.as_view(str(u'csc_perform_reset'))),

        ]
        for rule in rules:
            blueprint.add_url_rule(*rule)

        return blueprint


    # ###############################################
    # IAuthFunctions
    # ###############################################

    def get_auth_functions(self):
        unauthorized = lambda context, data_dict: {'success': False}
        authorized = lambda context, data_dict: {'success': True}
        return {
            'csc_package_activity_list_html': csc_auth_package_activity_list_html,
            'csc_group_activity_list_html': csc_auth_group_activity_list_html,
            'csc_organization_activity_list_html': csc_auth_organization_activity_list_html,
            }


def csc_local_url(url_to_amend, **kw):
    default_locale = False
    locale = kw.pop('locale', None)
    no_root = kw.pop('__ckan_no_root', False)
    allowed_locales = ['default'] + i18n.get_locales()
    if locale and locale not in allowed_locales:
        locale = None
    if locale:
        if locale == 'default':
            default_locale = True
    else:
        try:
            locale = request.environ.get('CKAN_LANG')
            default_locale = request.environ.get('CKAN_LANG_IS_DEFAULT', True)
        except TypeError:
            default_locale = True
    root = ''
    if kw.get('qualified', False):
        # if qualified is given we want the full url ie http://...
        protocol, host = ckan_helpers.get_site_protocol_and_host()
        root = ckan_helpers._routes_default_url_for('/',
                                       qualified=True,
                                       host=host,
                                       protocol=protocol)[:-1]
    url_path = url_to_amend[len(root):]

    # ckan.root_path is defined when we have none standard language
    # position in the url
    root_path = config.get('ckan.root_path', None)
    context_root_path = ''
    if root_path:
        context_root_path = re.sub('/{{LANG}}', '', root_path)
        if default_locale:
            root_path = re.sub('/{{LANG}}', '', root_path)
        else:
            root_path = re.sub('{{LANG}}', str(locale), root_path)
        complete_root_path = root_path + context_root_path + '/'
        if (url_path.startswith(complete_root_path)):
            #url_to_amend = url_to_amend.replace(complete_root_path, root_path + '/', 1)
            url_path = url_path[len(complete_root_path):]
        elif (url_path.startswith(context_root_path + '/')):
            url_path = url_path[len(context_root_path):]
            
    
    #url_path = url_to_amend[len(root):]
    #log.info("url_path=%s", url_path)
    url = '%s%s%s' % (root, root_path, url_path)

    # stop the root being added twice in redirects
    if no_root and url_to_amend.startswith(root):
        url = url_to_amend[len(root):]
        if not default_locale:
            url = '/%s%s' % (locale, url)

    if url == '/packages':
        error = 'There is a broken url being created %s' % kw
        raise CkanUrlException(error)       
    log.debug('[csc_local_url] from url %s to final url %s', url_to_amend, url)
    return url