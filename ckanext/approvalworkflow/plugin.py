import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.common import g

from ckanext.approvalworkflow.cli import get_commands
from ckanext.approvalworkflow import actions
from ckanext.approvalworkflow import auth
from ckanext.approvalworkflow import helpers
from ckanext.approvalworkflow import validators

# new blueprint
from ckanext.approvalworkflow.blueprints.approval_workflow_blueprint import approval_workflow as approval_workflow_blueprint
from ckanext.approvalworkflow.blueprints.organization_aw_blueprint import org_approval_workflow as org_approval_workflow
from ckanext.approvalworkflow.blueprints.aw_dataset_blueprint import dataset_approval_workflow as dataset_approval_workflow
from ckanext.approvalworkflow.blueprints.resource_blueprint import approval_resource_blueprint as approval_resource_blueprint


class ApprovalworkflowPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IDatasetForm, inherit=True)

    # IClick

    def get_commands(self):
        return get_commands()

    def is_fallback(self):
        return True

    def create_package_schema(self):
        schema = super().create_package_schema()
        schema['__after'].append(validators.validate_org_admin_state)
        return schema

    def update_package_schema(self):
        schema = super().update_package_schema()
        schema['__after'].append(validators.validate_org_admin_state)
        return schema

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def package_form(self):
        return super(ApprovalworkflowPlugin, self).package_form()


    def setup_template_variables(
            self, context, data_dict):
        return super(ApprovalworkflowPlugin, self).setup_template_variables(
                context, data_dict)

    def get_blueprint(self):
        return [approval_workflow_blueprint, org_approval_workflow,
                dataset_approval_workflow, approval_resource_blueprint]

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'approvalworkflow')
        toolkit.add_resource('assets', 'approvalworkflow')

    # IAction

    def get_actions(self):
        return {
            "workflow": actions.workflow,
            'package_update': actions.package_update,
            'save_workflow_options': actions.save_workflow_options,
            'approval_activity_create': actions.approval_activity_create,
            'approval_activity_read': actions.approval_activity_read,
        }

    # IAuthFunctions

    def get_auth_functions(self):
        return {
            "workflow": auth.workflow,
        }

    #  IValidators

    def get_validators(self):
        return {
            'validate_org_admin_state': validators.validate_org_admin_state,
        }

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'get_approvalworkflow_info': helpers.get_approvalworkflow_info,
            'get_approvalworkflow_org_info':
                helpers.get_approvalworkflow_org_info,
            'get_approval_org_info': helpers.get_approval_org_info,
            'is_user_org_admin': helpers.is_user_org_admin,
        }

    # IPackageController
    def create(self, entity):

        if entity.owner_org is None:
            org_admin = g.userobj.sysadmin
        else:
            org_admin = helpers.is_user_org_admin(
                entity.owner_org) or g.userobj.sysadmin
        if org_admin:
            pass
        else:
            entity.state = 'pending'

        return entity


def validate_state(key, data, errors, context):
    if "resources" not in data:
        data["state"] = "draft"
    else:
        data["state"] = "pending"
