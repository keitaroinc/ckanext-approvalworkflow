# Approval workflow functions
from flask import Blueprint
from flask.views import MethodView

import ckantoolkit as tk
from ckan.plugins import PluginImplementations, toolkit

# encoding: utf-8
import cgi
import json
import logging

import flask
from flask.views import MethodView

import six
import ckan.lib.base as base
import ckan.lib.datapreview as lib_datapreview
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.uploader as uploader
import ckan.lib.plugins as lib_plugins
from ckan.lib import mailer
import ckan.logic as logic
import ckan.model as model
import ckan.plugins as plugins
from ckan.common import _, g, request
from ckan.views.home import CACHE_PARAMETERS
from ckan.lib.search import SearchError, SearchQueryError, SearchIndexError
import ckan.lib.dictization.model_dictize as model_dictize

from ckan.views.dataset import (
    _get_pkg_template, _get_package_type, _setup_template_variables
)

import ckan.plugins.toolkit as toolkit

import ckan.lib.navl.dictization_functions
from ckan.common import config, asbool
import ckan.authz as authz
import ckan.lib.search as search

from ckanext.approvalworkflow import actions
import ckanext.approvalworkflow.helpers as aw_helpers
import ckanext.approvalworkflow.db as db
from ckanext.approvalworkflow.db import ApprovalWorkflow

_validate = ckan.lib.navl.dictization_functions.validate

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key

log = logging.getLogger(__name__)
from ckan.views.user import _extra_template_variables

approval_workflow = Blueprint('approval_workflow', __name__)


def _get_config_options():
    activity_workflow_options = [{
        u'value': u'1',
        u'text': (u'Deactivated')
    }, {
        u'value': u'2',
        u'text': (u'Activate '
                  u'for all datasets')
    }, {
        u'value': u'3',
        u'text': u'Activate per Organization'
    }]

    return dict(activity_workflow_options=activity_workflow_options)


class ApprovalConfigView(MethodView):
    def _prepare(self):
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'auth_user_obj': g.userobj,
        }

        user = context['user']
        sysadmin = authz.is_sysadmin(user)

        if not sysadmin:
            base.abort(403, _(u'Unauthorized'))
        return context

    def get(self):
        context = self._prepare()

        items = _get_config_options()
        data_dict = {u'user_obj': g.userobj, u'offset': 0}
        extra_vars = _extra_template_variables(context, data_dict)

        approval_workflow = ApprovalWorkflow.get()

        if approval_workflow:
            approval_workflow = db.table_dictize(approval_workflow, context)

            extra_vars['data'] = dict(items, **approval_workflow)
        else:
            extra_vars['data'] = dict(items)

        return tk.render(u'approval_workflow/snippets/approval_form.html', extra_vars=extra_vars)

    def post(self):
        context = self._prepare()
        try:
            req = request.form.copy()

            data_dict = logic.clean_dict(
                dict_fns.unflatten(
                    logic.tuplize_dict(
                        logic.parse_params(req,
                                           ignore_keys=CACHE_PARAMETERS))))

            del data_dict['save']
            data = actions.save_workflow_options(self, context, data_dict)

        except logic.ValidationError as e:
            items = _get_config_options()
            data = request.form
            errors = e.error_dict
            error_summary = e.error_summary
            vars = dict(data=data,
                        errors=errors,
                        error_summary=error_summary,
                        form_items=items,
                        **items)
            return base.render(u'approval_workflow/snippets/approval_form.html', extra_vars=vars)

        return h.redirect_to(u'approval_workflow.config')

approval_workflow.add_url_rule(u'/workflow', view_func=ApprovalConfigView.as_view(str(u'config')))


def index(data=None):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'auth_user_obj': g.userobj,
        u'for_view': True
    }
    
    data = _get_config_options()

    data_dict = {u'user_obj': g.userobj, u'offset': 0}
    extra_vars = _extra_template_variables(context, data_dict)
    extra_vars['data'] = data

    if tk.request.method == 'POST' and not data:
        print(POST)

    return tk.render('approval_workflow/index.html', extra_vars=extra_vars)


def datasets():
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'auth_user_obj': g.userobj,
        u'for_view': True
    }

    data = _get_config_options()
    data_dict_user = {u'user_obj': g.userobj, u'include_datasets': True, u'include_private': True, u'include_review': True}

    approval_workflow = ApprovalWorkflow.get()

    if approval_workflow:
        approval_workflow = db.table_dictize(approval_workflow, context)

        if approval_workflow['active'] == True:
            extra_vars = approval_extra_template_variables(context, data_dict_user)

            data_dict = extra_vars['user_dict']

            vars = dict(context=context,
                        user_dict = extra_vars['user_dict'],
                        is_sysadmin = extra_vars['is_sysadmin'],
                        data=data,
                        data_dict=data_dict)

            return tk.render(u'approval_workflow/dashboard.html', extra_vars=vars)
        else:
            data_dict = {u'user_obj': g.userobj}
            extra_vars = _extra_template_variables(context, data_dict)
            extra_vars['data'] = data
            return tk.render(u'approval_workflow/snippets/not_active.html', extra_vars=extra_vars)
    else:
        data_dict = {u'user_obj': g.userobj}
        extra_vars = _extra_template_variables(context, data_dict)
        extra_vars['data'] = data
        return tk.render(u'approval_workflow/snippets/not_active.html', extra_vars=extra_vars)


def package_review_search(context, data_dict):
    # sometimes context['schema'] is None
    schema = (context.get('schema') or
              logic.schema.default_package_search_schema())
    data_dict, errors = _validate(data_dict, schema, context)
    # put the extras back into the data_dict so that the search can
    # report needless parameters
    data_dict.update(data_dict.get('__extras', {}))
    data_dict.pop('__extras', None)
    if errors:
        raise ValidationError(errors)

    model = context['model']
    session = context['session']
    user = context.get('user')

    logic.check_access('package_search', context, data_dict)

    # Move ext_ params to extras and remove them from the root of the search
    # params, so they don't cause and error
    data_dict['extras'] = data_dict.get('extras', {})
    for key in [key for key in data_dict.keys() if key.startswith('ext_')]:
        data_dict['extras'][key] = data_dict.pop(key)

    # set default search field
    data_dict['df'] = 'text'

    # check if some extension needs to modify the search params
    for item in plugins.PluginImplementations(plugins.IPackageController):
        data_dict = item.before_search(data_dict)

    # the extension may have decided that it is not necessary to perform
    # the query
    abort = data_dict.get('abort_search', False)

    if data_dict.get('sort') in (None, 'rank'):
        data_dict['sort'] = config.get('ckan.search.default_package_sort') or 'score desc, metadata_modified desc'

    results = []
    if not abort:
        if asbool(data_dict.get('use_default_schema')):
            data_source = 'data_dict'
        else:
            data_source = 'validated_data_dict'
        data_dict.pop('use_default_schema', None)

        result_fl = data_dict.get('fl')
        if not result_fl:
            data_dict['fl'] = 'id {0}'.format(data_source)
        else:
            data_dict['fl'] = ' '.join(result_fl)

        include_private = asbool(data_dict.pop('include_private', False))
        include_drafts = asbool(data_dict.pop('include_drafts', False))
        include_review = asbool(data_dict.pop('include_review', False))

        data_dict.setdefault('fq', '')
        if not include_private:
            data_dict['fq'] = '+capacity:public ' + data_dict['fq']
        if include_review:
            data_dict['fq'] += '+state:(pending)'

        # Pop these ones as Solr does not need them
        extras = data_dict.pop('extras', None)

        # enforce permission filter based on user
        if context.get('ignore_auth') or (user and authz.is_sysadmin(user)):
            labels = None
        else:
            labels = lib_plugins.get_permission_labels(
                ).get_user_dataset_labels(context['auth_user_obj'])

        query = search.query_for(model.Package)
        query.run(data_dict, permission_labels=labels)

        print(query.results)
        
        # Add them back so extensions can use them on after_search
        data_dict['extras'] = extras

        if result_fl:
            for package in query.results:
                if isinstance(package, text_type):
                    package = {result_fl[0]: package}
                extras = package.pop('extras', {})
                package.update(extras)
                results.append(package)
        else:
            for package in query.results:
                # get the package object
                package_dict = package.get(data_source)
                # use data in search index if there
                if package_dict:
                    # the package_dict still needs translating when being viewed
                    package_dict = json.loads(package_dict)
                    if context.get('for_view'):
                        for item in plugins.PluginImplementations(
                                plugins.IPackageController):
                            package_dict = item.before_view(package_dict)
                    results.append(package_dict)
                else:
                    log.error('No package_dict is coming from solr for package '
                              'id %s', package['id'])

        count = query.count
        facets = query.facets
    else:
        count = 0
        facets = {}
        results = []

    search_results = {
        'count': count,
        'facets': facets,
        'results': results,
        'sort': data_dict['sort']
    }

    print(search_results)

    # create a lookup table of group name to title for all the groups and
    # organizations in the current search's facets.
    group_names = []
    for field_name in ('groups', 'organization'):
        group_names.extend(facets.get(field_name, {}).keys())

    groups = (session.query(model.Group.name, model.Group.title)
                    .filter(model.Group.name.in_(group_names))
                    .all()
              if group_names else [])
    group_titles_by_name = dict(groups)

    # Transform facets into a more useful data structure.
    restructured_facets = {}
    for key, value in facets.items():
        restructured_facets[key] = {
            'title': key,
            'items': []
        }
        for key_, value_ in value.items():
            new_facet_dict = {}
            new_facet_dict['name'] = key_
            if key in ('groups', 'organization'):
                display_name = group_titles_by_name.get(key_, key_)
                display_name = display_name if display_name and display_name.strip() else key_
                new_facet_dict['display_name'] = display_name
            elif key == 'license_id':
                license = model.Package.get_license_register().get(key_)
                if license:
                    new_facet_dict['display_name'] = license.title
                else:
                    new_facet_dict['display_name'] = key_
            else:
                new_facet_dict['display_name'] = key_
            new_facet_dict['count'] = value_
            restructured_facets[key]['items'].append(new_facet_dict)
    search_results['search_facets'] = restructured_facets

    # check if some extension needs to modify the search results
    for item in plugins.PluginImplementations(plugins.IPackageController):
        search_results = item.after_search(search_results, data_dict)

    # After extensions have had a chance to modify the facets, sort them by
    # display name.
    for facet in search_results['search_facets']:
        search_results['search_facets'][facet]['items'] = sorted(
            search_results['search_facets'][facet]['items'],
            key=lambda facet: facet['display_name'], reverse=True)

    return search_results


def approval_user_show(context, data_dict):
    '''Return a user account.

    Either the ``id`` or the ``user_obj`` parameter must be given.

    :param id: the id or name of the user (optional)
    :type id: string
    :param user_obj: the user dictionary of the user (optional)
    :type user_obj: user dictionary
    :param include_datasets: Include a list of datasets the user has created.
        If it is the same user or a sysadmin requesting, it includes datasets
        that are draft or private.
        (optional, default:``False``, limit:50)
    :type include_datasets: bool
    :param include_num_followers: Include the number of followers the user has
        (optional, default:``False``)
    :type include_num_followers: bool
    :param include_password_hash: Include the stored password hash
        (sysadmin only, optional, default:``False``)
    :type include_password_hash: bool
    :param include_plugin_extras: Include the internal plugin extras object
        (sysadmin only, optional, default:``False``)
    :type include_plugin_extras: bool


    :returns: the details of the user. Includes email_hash and
        number_created_packages (which excludes draft or private datasets
        unless it is the same user or sysadmin making the request). Excludes
        the password (hash) and reset_key. If it is the same user or a
        sysadmin requesting, the email and apikey are included.
    :rtype: dictionary

    '''
    model = context['model']

    id = data_dict.get('id', None)
    provided_user = data_dict.get('user_obj', None)
    if id:
        user_obj = model.User.get(id)
        context['user_obj'] = user_obj
    elif provided_user:
        context['user_obj'] = user_obj = provided_user
    else:
        raise NotFound

    logic.check_access('user_show', context, data_dict)

    if not bool(user_obj):
        raise NotFound

    requester = context.get('user')
    sysadmin = False
    if requester:
        sysadmin = authz.is_sysadmin(requester)
        requester_looking_at_own_account = requester == user_obj.name
        include_private_and_draft_datasets = (
            sysadmin or requester_looking_at_own_account)
    else:
        include_private_and_draft_datasets = False
    context['count_private_and_draft_datasets'] = \
        include_private_and_draft_datasets

    include_password_hash = sysadmin and asbool(
        data_dict.get('include_password_hash', False))

    include_plugin_extras = sysadmin and asbool(
        data_dict.get('include_plugin_extras', False))

    user_dict = model_dictize.user_dictize(
        user_obj, context, include_password_hash, include_plugin_extras)

    if context.get('return_minimal'):
        log.warning('Use of the "return_minimal" in user_show is '
                    'deprecated.')
        return user_dict

    if asbool(data_dict.get('include_datasets', False)):
        user_dict['datasets'] = []
        include_review = sysadmin and asbool(
            data_dict.get('include_review', False))

        #fq = "+creator_user_id:{0}".format(user_dict['id'])
        fq = ""

        search_dict = {'rows': 50}

        if include_private_and_draft_datasets:
            search_dict.update({
                'include_private': True,
                'include_drafts': True})

        if include_review:
            if include_private_and_draft_datasets:
                search_dict.update({
                    'include_private': True,
                    'include_review': True})                
            else:
                search_dict.update({
                    'include_private': True,
                    'include_review': True})

        search_dict.update({'fq': fq})
        print (search_dict)
        user_dict['datasets'] = package_review_search(context, search_dict)['results']
        print (user_dict['datasets'])
    
    return user_dict


def approval_extra_template_variables(context, data_dict):
    is_sysadmin = authz.is_sysadmin(g.user)
    try:
        user_dict = approval_user_show(context, data_dict)
    except logic.NotFound:
        base.abort(404, _(u'User not found'))
    except logic.NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))

    is_myself = user_dict[u'name'] == g.user
    about_formatted = h.render_markdown(user_dict[u'about'])
    extra = {
        u'is_sysadmin': is_sysadmin,
        u'user_dict': user_dict,
        u'is_myself': is_myself,
        u'about_formatted': about_formatted
    }
    return extra


approval_workflow.add_url_rule(u'/workflow/datasets', view_func=datasets)
