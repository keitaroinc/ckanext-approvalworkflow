from ckan.common import g
import ckan.plugins.toolkit as toolkit
import ckan.plugins as p
import ckanext.approvalworkflow.db as db
import ckan.logic as logic
import datetime
from ckan.model.types import make_uuid
from ckanext.approvalworkflow.db import ApprovalWorkflowDataset
from ckanext.approvalworkflow import helpers

ValidationError = toolkit.ValidationError
asbool = toolkit.asbool
NotFound = logic.NotFound


def workflow(self, context):
    session = context.get('session')
    approval_workflow = ApprovalWorkflow()

    return


def save_workflow_options(self, context, data_dict):
    session = context.get('session')
    userobj = context.get("auth_user_obj", None)
    model = context.get("model")

    if not userobj:
        raise NotFound(toolkit._('User not found'))

    db_model = db.ApprovalWorkflow().get()

    if not db_model:
        db_model = db.ApprovalWorkflow()

    aw_active = data_dict.get("approval_workflow_active")

    if aw_active != '1':
        db_model.active = True
        db_model.approval_workflow_active = aw_active
        db_model.deactivate_edit = bool(data_dict.get("ckan.edit-button"))

        if aw_active == '3':
            db_model.active_per_organization = True
        else:
            db_model.active_per_organization = False
    else:
        db_model.active = False
        db_model.approval_workflow_active = aw_active
        db_model.active_per_organization = False
        db_model.deactivate_edit = False

        # find Organizations
        aw_org_model = db.ApprovalWorkflowOrganization.approval_workflow_organization(approvalworkflow_id=db_model.id)

        if aw_org_model:
            for org in aw_org_model:
                org.active = False
                org.deactivate_edit = False
                org.org_approval_workflow_active = aw_active
                org.save()

    db_model.save()
    return


def save_org_workflow_options(self, context, data_dict):
    session = context.get('session')
    userobj = context.get("auth_user_obj", None)
    organization = data_dict['organization']

    if not userobj:
        raise NotFound(toolkit._('User not found'))

    approval_workflow = db.ApprovalWorkflow().get()

    if approval_workflow:
        aw_dict = db.table_dictize(approval_workflow, context)

        db_model = db.ApprovalWorkflowOrganization.get(organization_id=organization)

        if not db_model:
            db_model = db.ApprovalWorkflowOrganization()

        aw_active = data_dict.get("approval_workflow_active")

        if aw_active == '2':
            db_model.active = True
            db_model.approval_workflow_id = approval_workflow
            db_model.organization_id = organization
            db_model.org_approval_workflow_active = aw_active
            db_model.deactivate_edit = bool(data_dict.get("ckan.edit-button"))
        else:
            db_model.active = False
            db_model.approval_workflow_id = approval_workflow
            db_model.org_approval_workflow_active = aw_active
            db_model.organization_id = organization
            db_model.deactivate_edit = False

        db_model.save()
    return


@p.toolkit.chained_action
def package_update(up_func, context, data_dict):

    if data_dict[u'owner_org'] is None:
        org_admin = g.userobj.sysadmin
    else:
        org_admin = helpers.is_user_org_admin(
            data_dict[u'owner_org']) or g.userobj.sysadmin

    if org_admin:
        pass
    else:
        data_dict['state'] = 'pending'
    dataset_dict = up_func(context, data_dict)
    return dataset_dict


def approval_activity_create(context, data_dict):
    session = context.get('session')
    if g.userobj:
        user_name = g.userobj.name
    else:
        user_name = 'not logged in'

    try:
        activity_workflow_dataset = ApprovalWorkflowDataset()
        activity_workflow_dataset.id = make_uuid()
        activity_workflow_dataset.package_id = data_dict['package_id']
        activity_workflow_dataset.user_name = user_name
        activity_workflow_dataset.timestamp = str(datetime.datetime.now())
        activity_workflow_dataset.status = data_dict['submitted_action']
        activity_workflow_dataset.approval_notes = data_dict['approval-notes']
        session.add(activity_workflow_dataset)
        session.commit()

    except Exception as e:
        # log.error(f"Error saving approval workflow dataset: {e}")
        session.rollback()

    return


def approval_activity_read(context, package_id):

    session = context.get("session")

    approval_stream = (
        session.query(ApprovalWorkflowDataset)
        .filter_by(package_id=package_id)
        .order_by(ApprovalWorkflowDataset.timestamp.desc())
        .all()
    )

    return approval_stream
