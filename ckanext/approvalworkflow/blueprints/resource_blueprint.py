# Resource related blueprint
# Overriding Resource functions
import six
import cgi
from flask import Blueprint
from ckan.common import g, request
import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.model as model
import ckan.views.resource as resource

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
    url_prefix=u'/dataset/<id>/resource',
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
        resource_id = data.pop(u'id')

        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'auth_user_obj': g.userobj
        }

        data_provided = False
        for key, value in six.iteritems(data):
            if (
                    (value or isinstance(value, cgi.FieldStorage))
                    and key != u'resource_type'):
                data_provided = True
                break

        if save_action == u'review':
            # XXX race condition if another user edits/deletes
            data_dict = get_action(u'package_show')(context, {u'id': id})
            get_action(u'package_update')(
                dict(context, allow_state_change=True),
                dict(data_dict, state=u'pending')
            )
            import ckanext.approvalworkflow.email as email
            user = get_sysadmins()

            org = get_action(u'organization_show')(context, {u'id': data_dict['owner_org']})
            for user in user:
                if user.email:
                    email.send_approval_needed(user, org, data_dict)
            return h.redirect_to(u'{}.read'.format(package_type), id=id)         

        else:
            return super(CreateView, self).post(package_type, id)

    def get(self, package_type, id, data=None, errors=None, error_summary=None):
        return super(CreateView, self).get(package_type, id, data, errors, error_summary)


def get_sysadmins():
    q = model.Session.query(model.User).filter(model.User.sysadmin == True,
                                               model.User.state == 'active')
    return q.all()


def register_dataset_plugin_rules(blueprint):
    blueprint.add_url_rule(u'/new', view_func=CreateView.as_view(str(u'new')))


register_dataset_plugin_rules(approval_resource_blueprint)
