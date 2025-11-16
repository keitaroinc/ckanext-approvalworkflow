# Approval workflow functions
from flask import Blueprint
from flask.views import MethodView
from typing import Union
from ckan.types import Response
import logging
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.model as model
from ckan.common import _, g, request
from ckan.lib.search import SearchIndexError
from ckan.views.dataset import (
    _get_pkg_template, _get_package_type, _setup_template_variables
)
import ckan.lib.navl.dictization_functions
import ckan.views.dataset as dataset


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


dataset_approval_workflow = Blueprint(
    u'dataset_approval_workflow',
    __name__,
    url_prefix=u'/dataset',
    url_defaults={u'package_type': u'dataset'}
)


# class ApprovalWorkflowRejectView(MethodView):
#     def _prepare(self):
#         context = {
#             u'model': model,
#             u'session': model.Session,
#             u'user': g.user,
#             u'auth_user_obj': g.userobj
#         }
#         return context

#     def post(self, package_type, id):
#         if u'cancel' in request.form:
#             return h.redirect_to(u'{}.edit'.format(package_type), id=id)
#         context = self._prepare()
#         try:
#             pkg = get_action(u'package_show')(context, {u'id': id})
#             pkg['state'] = u'draft'
#             pkg_dict = get_action(u'package_update')(context, pkg)
#         except NotFound:
#             return base.abort(404, _(u'Dataset not found'))
#         except NotAuthorized:
#             return base.abort(
#                 403,
#                 _(u'Unauthorized to edit package %s') % u''
#             )

#         h.flash_notice(_(u'Dataset has been rejected. Saved as Draft'))
#         return h.redirect_to(u'dataset.search')

#     def get(self, package_type, id):
#         context = self._prepare()
#         try:
#             pkg_dict = get_action(u'package_show')(context, {u'id': id})
#         except NotFound:
#             return base.abort(404, _(u'Dataset not found'))
#         except NotAuthorized:
#             return base.abort(
#                 403,
#                 _(u'Unauthorized to delete package %s') % u''
#             )

#         dataset_type = pkg_dict[u'type'] or package_type

#         # TODO: remove
#         g.pkg_dict = pkg_dict

#         return base.render(
#             u'package/confirm_reject.html', {
#                 u'pkg_dict': pkg_dict,
#                 u'dataset_type': dataset_type
#             }
#         )


class DatasetApproval(MethodView):
    def _prepare(self):
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'auth_user_obj': g.userobj,
            u'form_style': u'edit'
        }
        return context

    def get(
        self, package_type, id, data=None, errors=None, error_summary=None
    ):
        context = self._prepare()
        package_type = _get_package_type(id) or package_type
        try:
            pkg_dict = get_action(u'package_show')(context, {u'id': id})
        except NotFound:
            return base.abort(404, _(u'Dataset not found'))
        except NotAuthorized:
            return base.abort(
                403,
                _(u'Unauthorized to delete package %s') % u''
            )

        dataset_type = pkg_dict[u'type'] or package_type

        return base.render(
            u'package/snippets/package_approval_form.html',
            {
                u'pkg_dict': pkg_dict,
                u'dataset_type': dataset_type
            }
        )

    def post(self, package_type, id):

        context = self._prepare()
        approval_notes = tk.request.form.get('approval-notes')
        submitted_action = tk.request.form.get('action')
        # if u'cancel' in request.form:
        #     return h.redirect_to(u'{}.edit'.format(package_type), id=id)
        try:
            pkg = get_action(u'package_show')(context, {u'id': id})
            if submitted_action == 'approved':
                pkg['state'] = u'active'
                get_action(u'package_update')(context, pkg)
            elif submitted_action == 'rejected':
                pkg['state'] = u'draft'
                get_action(u'package_update')(context, pkg)
        except NotFound:
            return base.abort(404, _(u'Dataset not found'))
        except NotAuthorized:
            return base.abort(
                403,
                _(u'Unauthorized to edit package %s') % u''
            )
        data_dict = {
            'package_id': pkg['id'],
            'approval-notes': approval_notes,
            'submitted_action': submitted_action
        }
        get_action(u'approval_activity_create')(context, data_dict)

        h.flash_notice(_(u'Dataset has been {}.'.format(submitted_action)))
        return h.redirect_to(u'dataset.search')


# dataset_approval_workflow.add_url_rule(
#     u'/reject/<id>', view_func=ApprovalWorkflowRejectView.as_view(str(u'reject'))
# )

dataset_approval_workflow.add_url_rule(
    u'/datasetapproval/<id>',
    view_func=DatasetApproval.as_view(str(u'datasetapproval'))
)
