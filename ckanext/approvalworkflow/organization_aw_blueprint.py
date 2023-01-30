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
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.uploader as uploader
from ckan.lib import mailer
import ckan.logic as logic
import ckan.model as model
import ckan.plugins as plugins
from ckan.common import _, g, request
from ckan.views.home import CACHE_PARAMETERS
from ckan.lib.search import SearchError, SearchQueryError, SearchIndexError

from ckan.views.dataset import (
    _get_pkg_template, _get_package_type, _setup_template_variables
)

import ckan.plugins.toolkit as toolkit

import ckan.lib.navl.dictization_functions
from ckan.common import config, asbool
import ckan.authz as authz
import ckan.lib.search as search

from ckanext.approvalworkflow import actions
import ckanext.approvalworkflow.db as db
from ckanext.approvalworkflow.db import ApprovalWorkflowOrganization

_validate = ckan.lib.navl.dictization_functions.validate

Blueprint = flask.Blueprint
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key

log = logging.getLogger(__name__)


org_approval_workflow = Blueprint('org_approval_workflow', __name__)

def _get_config_options():
    org_activity_workflow_options = [{
        u'value': u'1',
        u'text': (u'Deactivated')
    }, {
        u'value': u'2',
        u'text': (u'Activate')
    }]

    return dict(org_activity_workflow_options=org_activity_workflow_options)


class OrganizationApprovalConfigView(MethodView):
    def _prepare(self, id):
        data_dict = {u'id': id, u'include_datasets': False}

        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'auth_user_obj': g.userobj,
            u'id': id
        }

        try:
            logic.get_action(u'organization_show')(context, data_dict)
            logic.check_access(u'organization_update', context, {u'id': id})
        except NotAuthorized:
            base.abort(403, _(u'Unauthorized'))
        except NotFound:
            base.abort(404, _(u'Organization not found'))
        return context

    def get(self, id=None):
        context = self._prepare(id)
        items = _get_config_options()
        data_dict = {u'user_obj': g.userobj, u'id': id}

        group_type = u'organization'
        group_dict = _get_group_dict(id, group_type)

        g.group_dict = group_dict
        g.group_type = group_type

        db_model = db.ApprovalWorkflowOrganization.get(organization_id=group_dict['id'])
        
        if db_model:
            model_dict = db.table_dictize(db_model, context)

            extra_vars = {u"group_dict": group_dict,
                        u"group_type": group_type,
                        u'data_dict': model_dict,
                        u'data': items}
        else:
            extra_vars = {u"group_dict": group_dict,
                        u"group_type": group_type,
                        u'data_dict': data_dict,
                        u'data': items}            

        return tk.render(u'organization/snippets/org_approval_form.html', extra_vars=extra_vars)

    def post(self, id=None):
        context = self._prepare(id)
        items = _get_config_options()
        model_dict = []

        group_type = u'organization'
        group_dict = _get_group_dict(id, group_type)

        g.group_dict = group_dict
        g.group_type = group_type

        db_model = db.ApprovalWorkflowOrganization.get(organization_id=group_dict['id'])

        try:
            req = request.form.copy()

            data_dict = logic.clean_dict(
                dict_fns.unflatten(
                    logic.tuplize_dict(
                        logic.parse_params(req,
                                           ignore_keys=CACHE_PARAMETERS))))
            data_dict['organization'] = group_dict['id']
            

            del data_dict['save']
            data = actions.save_org_workflow_options(self, context, data_dict)


        except logic.ValidationError as e:
            if db_model:
                model_dict = db.table_dictize(db_model, context)            
            data = request.form
            errors = e.error_dict
            error_summary = e.error_summary
            vars = dict(data=data,
                        errors=errors,
                        error_summary=error_summary,
                        form_items=items,
                        data_dict=model_dict,
                        **items)
            return tk.render(u'organization/snippets/org_approval_form.html', extra_vars=vars)

        if db_model:
            model_dict = db.table_dictize(db_model, context)  
        vars = dict(data=items,
                    form_items=items,
                    group_dict=group_dict,
                    group_type=group_type,
                    data_dict=model_dict,
                    **items)
        return tk.render(u'organization/snippets/org_approval_form.html', extra_vars=vars)

def _get_group_dict(id, group_type):
    u''' returns the result of group_show action or aborts if there is a
    problem '''
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True
    }
    try:
        return logic.get_action(u'organization_show')(context, {
            u'id': id,
            u'include_datasets': False
        })
    except (NotFound, NotAuthorized):
        base.abort(404, _(u'Group not found'))
  
org_approval_workflow.add_url_rule(u'/organization/approval_workflow/<id>', view_func=OrganizationApprovalConfigView.as_view(str(u'approval_workflow')))

def index(data=None, id=None):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'auth_user_obj': g.userobj,
        u'for_view': True,
        u'id': id
    }

    data_dict = {u'user_obj': g.userobj, u'id': id}
    extra_vars = _extra_template_variables(context, data_dict)

    if tk.request.method == 'POST' and not data:
        return 
        
    return tk.render(u'organization/snippets/org_approval_form.html', extra_vars=extra_vars)