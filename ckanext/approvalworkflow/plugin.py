import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.common import _, g
import logging

from ckanext.approvalworkflow.cli import get_commands
from ckanext.approvalworkflow import actions
from ckanext.approvalworkflow import auth
from ckanext.approvalworkflow import helpers
from ckanext.approvalworkflow.blueprints.approval_workflow_blueprint import approval_workflow as approval_workflow_blueprint
from ckanext.approvalworkflow.blueprints.organization_aw_blueprint import org_approval_workflow as org_approval_workflow
from ckanext.approvalworkflow.blueprints.aw_dataset_blueprint import dataset_approval_workflow as dataset_approval_workflow

log = logging.getLogger(__name__)


class ApprovalworkflowPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IClick

    def get_commands(self):
        return get_commands()

    # IBlueprint

    def get_blueprint(self):
        return [approval_workflow_blueprint, org_approval_workflow,
                dataset_approval_workflow]

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
            'save_workflow_options': actions.save_workflow_options,
            'approval_activity_create': actions.approval_activity_create,
            'approval_activity_read': actions.approval_activity_read,
        }

    # IAuthFunctions

    def get_auth_functions(self):
        return {
            "workflow": auth.workflow,
        }

    def get_helpers(self):
        return {
            'get_approvalworkflow_info': helpers.get_approvalworkflow_info,
            'get_approvalworkflow_org_info':
                helpers.get_approvalworkflow_org_info,
            'get_approval_org_info': helpers.get_approval_org_info,
            'is_user_org_admin': helpers.is_user_org_admin,
            'get_org_approval_info': helpers.get_org_approval_info,
        }

    # IPackageController

    def create(self, entity):

        if entity.private:
            return entity

        owner_org = entity.owner_org

        if not owner_org:
            log.info("Dataset has no owner organization, skipping approval check")
            return entity

        is_org_admin = helpers.is_user_org_admin(owner_org)
        is_sysadmin = g.userobj and g.userobj.sysadmin

        if not (is_org_admin or is_sysadmin):
            log.info(
                "Dataset created by non-admin user, "
                "requires approval for public visibility"
            )
            entity.private = True
            flash_msg = _(
                "Your dataset has been set as private and "
                "requires approval to be made public."
            )
            toolkit.h.flash_notice(flash_msg)

        return entity

    def edit(self, entity):

        if entity.private:
            return entity

        owner_org = entity.owner_org
        if not owner_org:
            log.info("Dataset has no owner organization, skipping approval check")
            return entity

        is_org_admin = helpers.is_user_org_admin(owner_org)
        is_sysadmin = g.userobj and g.userobj.sysadmin

        if not (is_org_admin or is_sysadmin):
            log.info(
                "Dataset updated by non-admin user, "
                "requires approval for public visibility"
            )
            entity.private = True
            flash_msg = _(
                "Your dataset has been set as private and "
                "requires approval to be made public."
            )
            toolkit.h.flash_notice(flash_msg)
        return entity
