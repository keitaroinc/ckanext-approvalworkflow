from ckan.common import g
import ckan.plugins.toolkit as toolkit
import ckan.plugins as p
import ckanext.approvalworkflow.db as db
import ckan.logic as logic

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
    dataset_dict = up_func(context, data_dict)
    # name_or_id = data_dict.get('id') or data_dict.get('name')
    # model = context['model']
    # session = context['session']
    # name_or_id = data_dict.get('id') or data_dict.get('name')

    # if name_or_id is None:
    #     raise ValidationError({'id': _('Missing value')})

    # pkg = model.Package.get(name_or_id)
    # if pkg is None:
    #     raise NotFound(_('Package was not found.'))
    # context["package"] = pkg

    # if g.userobj:
    #     user_id = g.userobj.id
    # else:
    #     user_id = 'not logged in'
    # breakpoint()
    # activity = pkg.activity_stream_item('changed1', user_id)
    # session.add(activity)
    print("==========================================================")
    print("PACKAGE UPDATE ACTION FROM APPROVAL WORKFLOW EXTENSION")
    print("==========================================================")
    return dataset_dict
