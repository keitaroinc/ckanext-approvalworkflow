from flask import Blueprint
from flask.views import MethodView

import ckantoolkit as tk

import logging

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.model as model
from ckan.common import _, g, request
from ckan.views.home import CACHE_PARAMETERS
import ckan.lib.navl.dictization_functions
import ckan.authz as authz

from ckanext.approvalworkflow import actions
import ckanext.approvalworkflow.db as db
from ckanext.approvalworkflow.db import ApprovalWorkflow
from ckan.views.user import _extra_template_variables

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key

log = logging.getLogger(__name__)

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
        log.info('No data received in POST request')

    return tk.render('approval_workflow/index.html', extra_vars=extra_vars)
