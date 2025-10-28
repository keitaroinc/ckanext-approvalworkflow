import ckantoolkit as tk
import ckan.plugins as p

config = ckantoolkit.config

_ = p.toolkit._


class ApprovalWorkflowController(p.toolkit.BaseController):
    def approval_wokflow_index(self):
        return workflow_index()


def workflow_index(self):
    return tk.render('approval_workflow/index.html')
