# Approval workflow functions
from flask import Blueprint
from flask.views import MethodView
import logging
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckanext.approvalworkflow.helpers as helpers
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import ckan.model as model
from ckan.common import _, g
from ckan.views.dataset import _get_package_type


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
                _(u'Unauthorized to edit package %s') % u''
            )

        dataset_type = pkg_dict[u'type'] or package_type
        org_admin = helpers.is_user_org_admin(
            pkg_dict[u'organization'][u'id']) or g.userobj.sysadmin
        if not org_admin:
            return base.abort(
                403,
                _(u'Unauthorized to approve package %s') % u''
            )

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
        try:
            pkg = get_action(u'package_show')(context, {u'id': id})
            breakpoint()
            if submitted_action == 'approved':
                get_action('package_patch')(
                    context, {'id': pkg['id'], 'private': False}
                    )
            elif submitted_action == 'rejected':
                get_action('package_patch')(
                    context, {'id': pkg['id'], 'private': True}
                    )
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
        try:
            get_action(u'approval_activity_create')(context, data_dict)
        except NotAuthorized:
            return base.abort(
                403,
                _(u'Unauthorized to approve package %s') % u''
            )

        h.flash_notice(_(u'Dataset has been {}.'.format(submitted_action)))
        return h.redirect_to(u'dataset.search')


class ApprovalStream(MethodView):

    def _prepare(self):
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'auth_user_obj': g.userobj,
        }

        return context

    def get(self, package_type, id):
        context = self._prepare()
        package_type = _get_package_type(id) or package_type
        try:
            pkg_dict = get_action(u'package_show')(context, {u'id': id})
        except NotFound:
            return base.abort(404, _(u'Dataset not found'))
        except NotAuthorized:
            return base.abort(
                403,
                _(u'Unauthorized to edit package %s') % u''
            )
        approval_stream = get_action(u'approval_activity_read')(context, pkg_dict['id'])
        return base.render(
            u'package/approval_stream.html',
            {
                u'pkg_dict': pkg_dict,
                u'approval_stream': approval_stream
            }
        )

    def post(self, package_type, id):
        pass


def request_dataset_review(id, package_type):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'auth_user_obj': g.userobj,
    }
    try:
        pkg_dict = get_action(u'package_show')(context, {u'id': id})
    except NotFound:
        return base.abort(404, _(u'Dataset not found'))
    except NotAuthorized:
        return base.abort(
            403,
            _(u'Unauthorized to edit package %s') % u''
        )

    # Create approval activity
    approval_data = {
        'package_id': pkg_dict['id'],
        'approval-notes': 'Dataset sent for approval',
        'submitted_action': 'pending',
    }
    get_action('approval_activity_create')(context, approval_data)

    # Notify org admins
    import ckanext.approvalworkflow.email as email

    org = get_action('organization_show')(context, {'id': pkg_dict['owner_org']})
    admins = helpers.get_org_admins_raw(org['id'])

    for user in admins:
        if user.email:
            email.send_approval_needed(user, org, pkg_dict)

    h.flash_notice(_(u'Dataset has {} been sent for review.'.format(pkg_dict['title'])))
    return h.redirect_to(u'dataset.read', id=pkg_dict['name'])


dataset_approval_workflow.add_url_rule(
    u'/datasetapproval/<id>',
    view_func=DatasetApproval.as_view(str(u'datasetapproval'))
)

dataset_approval_workflow.add_url_rule(
    u'/datasetapproval/activity/<id>',
    view_func=ApprovalStream.as_view(str(u'approvalstream'))
)

dataset_approval_workflow.add_url_rule(
    u'/datasetapproval/request_review/<id>',
    view_func=request_dataset_review)
