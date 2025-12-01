# Resource related blueprint
# Overriding Resource functions to add approval workflow functionality
from flask import Blueprint
from ckan.common import g, request
from ckanext.approvalworkflow import helpers
import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.model as model
import ckan.views.resource as resource
import ckan.plugins.toolkit as tk

clean_dict = logic.clean_dict
tuplize_dict = logic.tuplize_dict
parse_params = logic.parse_params
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError

approval_resource_blueprint = Blueprint(
    u'approval_dataset_resource',
    __name__,
    # url_prefix=u'/dataset/<id>/resource',
    url_defaults={u'package_type': u'dataset'}
)


class CreateView(resource.CreateView):
    def post(self, package_type, id):
        save_action = request.form.get(u'save')
        data = clean_dict(
            dict_fns.unflatten(tuplize_dict(parse_params(request.form)))
        )
        data.update(clean_dict(
            dict_fns.unflatten(tuplize_dict(parse_params(request.files)))
        ))
        del data[u'save']

        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'auth_user_obj': g.userobj
        }

        if save_action == u'review':
            # XXX race condition if another user edits/deletes
            data_dict = get_action(u'package_show')(context, {u'id': id})
            get_action(u'package_update')(
                dict(context, allow_state_change=True),
                dict(data_dict, state=u'pending')
            )

            approval_data = {
                'package_id': data_dict['id'],
                'approval-notes': 'Dataset sent for approval',
                'submitted_action': 'pending',
            }
            get_action(u'approval_activity_create')(context, approval_data)

            import ckanext.approvalworkflow.email as email

            org = get_action(u'organization_show')(context, {u'id': data_dict['owner_org']})

            admins = helpers.get_org_admins_raw(org['id'])
            for user in admins:
                if user.email:
                    email.send_approval_needed(user, org, data_dict)
            return h.redirect_to(u'{}.read'.format(package_type), id=id)

        else:
            return super(CreateView, self).post(package_type, id)

    def get(self, package_type, id, data=None, errors=None, error_summary=None):
        return super(CreateView, self).get(package_type, id, data, errors, error_summary)


def get_sysadmins():
    q = model.Session.query(model.User).filter(model.User.sysadmin is True,
                                               model.User.state == 'active')
    return q.all()


def register_dataset_plugin_rules(blueprint):
    blueprint.add_url_rule(
        u'/dataset/<id>/resource/new',
        view_func=CreateView.as_view(str(u'new'))
        )

    dataset_types = tk.config.get('ckanext.approvalworkflow.dataset_types', '')
    dataset_types = [dt.strip() for dt in dataset_types.split(',') if dt.strip()]

    if dataset_types:
        for dt in dataset_types:
            blueprint.add_url_rule(
                f'/{dt}/<id>/resource/new',
                view_func=CreateView.as_view(f'{dt}_resource_new')
            )


register_dataset_plugin_rules(approval_resource_blueprint)
