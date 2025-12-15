import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.common import g
import logging

from ckanext.approvalworkflow.cli import get_commands
from ckanext.approvalworkflow import actions
from ckanext.approvalworkflow import auth
from ckanext.approvalworkflow import helpers
from ckanext.approvalworkflow import validators

# new blueprint
from ckanext.approvalworkflow.blueprints.approval_workflow_blueprint import approval_workflow as approval_workflow_blueprint
from ckanext.approvalworkflow.blueprints.organization_aw_blueprint import org_approval_workflow as org_approval_workflow
from ckanext.approvalworkflow.blueprints.aw_dataset_blueprint import dataset_approval_workflow as dataset_approval_workflow

log = logging.getLogger(__name__)

class ApprovalworkflowPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IDatasetForm)

    # IClick

    def get_commands(self):
        return get_commands()
    
    def package_types(self):
        return ['dataset']

    def is_fallback(self):
        return False
    
    def create_package_schema(self):
        """
        Returns the schema for creating packages with custom validators.
        """
        log.info("=== create_package_schema called ===")
        
        # Get the default schema first
        schema = super(ApprovalworkflowPlugin, self).create_package_schema()
        
        log.info(f"Default private validators: {schema.get('private', [])}")
        
        # Apply your custom validator to the private field
        # Include standard validators before your custom one
        schema['private'] = [
            toolkit.get_validator('ignore_missing'),
            toolkit.get_validator('boolean_validator'),
            toolkit.get_validator('check_dataset_quality'),  # Your custom validator
        ]
        
        log.info(f"Applied validators to private field: {schema['private']}")
        
        # Add approval_workflow field to track approval status
        # Values: None (not submitted), 'approved', 'rejected'
        schema['approval_workflow'] = [
            toolkit.get_validator('ignore_missing'),
            toolkit.get_converter('convert_to_extras')
        ]
        
        return schema

    def update_package_schema(self):
        """
        Returns the schema for updating packages with custom validators.
        """
        log.info("=== update_package_schema called ===")
        
        # Get the default schema first
        schema = super(ApprovalworkflowPlugin, self).update_package_schema()
        
        log.info(f"Default private validators: {schema.get('private', [])}")
        
        # Apply your custom validator to the private field
        schema['private'] = [
            toolkit.get_validator('ignore_missing'),
            toolkit.get_validator('boolean_validator'),
            toolkit.get_validator('check_dataset_quality'),  # Your custom validator
        ]
        
        log.info(f"Applied validators to private field: {schema['private']}")
        
        # Add approval_workflow field
        schema['approval_workflow'] = [
            toolkit.get_validator('ignore_missing'),
            toolkit.get_converter('convert_to_extras')
        ]
        
        return schema

    def show_package_schema(self):
        """
        Returns the schema for showing packages.
        """
        schema = super(ApprovalworkflowPlugin, self).show_package_schema()
        
        schema['private'] = [
            toolkit.get_validator('ignore_missing'),
            toolkit.get_validator('boolean_validator'),
            toolkit.get_validator('datasets_with_no_organization_cannot_be_private')
        ]
        
        # Show approval_workflow from extras
        schema['approval_workflow'] = [
            toolkit.get_converter('convert_from_extras'),
            toolkit.get_validator('ignore_missing')
        ]

        return schema

    def setup_template_variables(
            self, context, data_dict):
        return super(ApprovalworkflowPlugin, self).setup_template_variables(
                context, data_dict)

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
       
    # IValidators
    def get_validators(self):
        """
        Register custom validators with CKAN.
        
        Returns a dictionary of validator names to validator functions.
        """
        return {
            'check_dataset_quality': validators.check_dataset_quality,
        }

    # IPackageController
    def before_dataset_create(self, context, data_dict):
        """
        Hook called before a dataset is created.
        Log the creation for debugging.
        """
        log.info("=" * 60)
        log.info("before_dataset_create called")
        log.info("=" * 60)
        log.info(f"Dataset name: {data_dict.get('name')}")
        log.info(f"Private value: {data_dict.get('private')}")
        log.info(f"Approval workflow: {data_dict.get('approval_workflow')}")
        
        return data_dict

    def after_dataset_create(self, context, pkg_dict):
        """
        Hook called after a dataset is created.
        
        NOTE: We no longer automatically set state to 'pending'.
        Datasets stay in 'active' state and use the approval_workflow field instead.
        """
        log.info("=" * 60)
        log.info("after_dataset_create called")
        log.info("=" * 60)
        log.info(f"Dataset: {pkg_dict.get('name')}")
        log.info(f"State: {pkg_dict.get('state')}")
        log.info(f"Private: {pkg_dict.get('private')}")
        log.info(f"Approval workflow: {pkg_dict.get('approval_workflow')}")
        
        # The approval workflow is now handled entirely through:
        # 1. The 'private' field (True/False)
        # 2. The 'approval_workflow' field (None, 'approved', 'rejected')
        # 3. The validator that checks permissions before allowing public datasets
        
        owner_org = pkg_dict.get('owner_org')
        if owner_org:
            is_org_admin = helpers.is_user_org_admin(owner_org)
            is_sysadmin = g.userobj and g.userobj.sysadmin
            
            if not (is_org_admin or is_sysadmin):
                log.info("Dataset created by non-admin user, requires approval for public visibility")

    def before_dataset_update(self, context, current, resource, data_dict):
        """
        Hook called before a dataset is updated.
        Log the update for debugging.
        """
        log.info("=" * 60)
        log.info("before_dataset_update called")
        log.info("=" * 60)
        log.info(f"Dataset: {data_dict.get('name')}")
        log.info(f"Old private: {current.get('private')}, New private: {data_dict.get('private')}")
        log.info(f"Old approval: {current.get('approval_workflow')}, New approval: {data_dict.get('approval_workflow')}")
        
        return data_dict

    def after_dataset_update(self, context, pkg_dict):
        """
        Hook called after a dataset is updated.
        """
        log.info("=" * 60)
        log.info("after_dataset_update called")
        log.info("=" * 60)
        log.info(f"Dataset: {pkg_dict.get('name')}")
        log.info(f"Private: {pkg_dict.get('private')}")
        log.info(f"Approval workflow: {pkg_dict.get('approval_workflow')}")
        
        return pkg_dict
