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

        save_action = request.form.get('save')

        data = clean_dict(
            dict_fns.unflatten(
                tuplize_dict(parse_params(request.form))
            )
        )
        data.update(clean_dict(
            dict_fns.unflatten(
                tuplize_dict(parse_params(request.files))
            )
        ))
        data.pop('save', None)  # Safe delete

        context = {
            'model': model,
            'session': model.Session,
            'user': g.user,
            'auth_user_obj': g.userobj
        }

        # 1) ALWAYS LET CKAN CREATE THE RESOURCE FIRST
        #    This avoids all partial-resource race conditions and ensures
        #    CKAN model observers see the correct state.

        result = super(CreateView, self).post(package_type, id)

        # 2) If this is a "review" submission, apply approval logic now,
        #    AFTER resource creation succeeded and was committed.

        if save_action == 'review':

            # Fetch the dataset AFTER the resource was created
            data_dict = get_action('package_show')(context, {'id': id})

            # Trigger approval workflow state changes
            get_action('package_update')(
                dict(context, allow_state_change=True),
                dict(data_dict, state='pending')
            )

            # Create approval activity
            approval_data = {
                'package_id': data_dict['id'],
                'approval-notes': 'Dataset sent for approval',
                'submitted_action': 'pending',
            }
            get_action('approval_activity_create')(context, approval_data)

            # Notify org admins
            import ckanext.approvalworkflow.email as email

            org = get_action('organization_show')(context, {'id': data_dict['owner_org']})
            admins = helpers.get_org_admins_raw(org['id'])

            for user in admins:
                if user.email:
                    email.send_approval_needed(user, org, data_dict)

            return h.redirect_to(f'{package_type}.read', id=id)

        # If not review → normal CKAN behavior applies
        return result


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
