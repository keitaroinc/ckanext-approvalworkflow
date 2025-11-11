# Approval workflow functions
from flask import Blueprint
from flask.views import MethodView
from typing import Union
from ckan.types import Response
import logging
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.model as model
from ckan.common import _, g, request
from ckan.lib.search import SearchIndexError
from ckan.views.dataset import (
    _get_pkg_template, _get_package_type, _setup_template_variables
)
import ckan.lib.navl.dictization_functions
import ckan.views.dataset as dataset


_validate = ckan.lib.navl.dictization_functions.validate

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


class EditView_(dataset.EditView):

    def post(self, package_type: str, id: str) -> Union[Response, str]:
        context = self._prepare()
        package_type = _get_package_type(id) or package_type
        log.debug(u'Package save request name: %s POST: %r', id, request.form)
        try:
            data_dict = clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.form)))
            )
        except dict_fns.DataError:
            return base.abort(400, _(u'Integrity Error'))
        try:
            if u'_ckan_phase' in data_dict:
                # we allow partial updates to not destroy existing resources
                context[u'allow_partial_update'] = True
                if u'tag_string' in data_dict:
                    data_dict[u'tags'] = dataset._tag_string_to_list(
                        data_dict[u'tag_string']
                    )
                del data_dict[u'_ckan_phase']
                del data_dict[u'save']
            data_dict['id'] = id
            breakpoint()
            data_dict['state'] = 'active'
            pkg_dict = get_action(u'package_update')(context, data_dict)

            return dataset._form_save_redirect(
                pkg_dict[u'name'], u'edit', package_type=package_type
            )
        except NotAuthorized:
            return base.abort(403, _(u'Unauthorized to read package %s') % id)
        except NotFound:
            return base.abort(404, _(u'Dataset not found'))
        except SearchIndexError as e:
            try:
                exc_str = str(repr(e.args))
            except Exception:  # We don't like bare excepts
                exc_str = str(str(e))
            return base.abort(
                500,
                _(u'Unable to update search index.') + exc_str
            )
        except ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(package_type, id, data_dict, errors, error_summary)

# class ApprovalEditView(MethodView):
#     def _prepare(self, id, data=None):
#         context = {
#             u'model': model,
#             u'session': model.Session,
#             u'user': g.user,
#             u'auth_user_obj': g.userobj,
#             u'save': u'save' in request.form
#         }
#         return context

#     def post(self, package_type, id):
#         context = self._prepare(id)
#         package_type = _get_package_type(id) or package_type
#         log.debug(u'Package save request name: %s POST: %r', id, request.form)
#         try:
#             data_dict = clean_dict(
#                 dict_fns.unflatten(tuplize_dict(parse_params(request.form)))
#             )
#         except dict_fns.DataError:
#             return base.abort(400, _(u'Integrity Error'))
#         try:
#             if u'_ckan_phase' in data_dict:
#                 # we allow partial updates to not destroy existing resources
#                 context[u'allow_partial_update'] = True
#                 if u'tag_string' in data_dict:
#                     data_dict[u'tags'] = dataset._tag_string_to_list(
#                         data_dict[u'tag_string']
#                     )
#                 del data_dict[u'_ckan_phase']
#                 del data_dict[u'save']
#             context[u'message'] = data_dict.get(u'log_message', u'')
#             data_dict['id'] = id
#             data_dict['state'] = 'active'
#             pkg_dict = get_action(u'package_update')(context, data_dict)

#             return dataset._form_save_redirect(
#                 pkg_dict[u'name'], u'edit', package_type=package_type
#             )
#         except NotAuthorized:
#             return base.abort(403, _(u'Unauthorized to read package %s') % id)
#         except NotFound:
#             return base.abort(404, _(u'Dataset not found'))
#         except SearchIndexError as e:
#             try:
#                 exc_str = text_type(repr(e.args))
#             except Exception:  # We don't like bare excepts
#                 exc_str = text_type(str(e))
#             return base.abort(
#                 500,
#                 _(u'Unable to update search index.') + exc_str
#             )
#         except ValidationError as e:
#             errors = e.error_dict
#             error_summary = e.error_summary
#             return self.get(package_type, id, data_dict, errors, error_summary)

#     def get(
#         self, package_type, id, data=None, errors=None, error_summary=None
#     ):
#         context = self._prepare(id, data)
#         package_type = _get_package_type(id) or package_type
#         try:
#             pkg_dict = get_action(u'package_show')(
#                 dict(context, for_view=True), {
#                     u'id': id
#                 }
#             )
#             context[u'for_edit'] = True
#             old_data = get_action(u'package_show')(context, {u'id': id})

#             if data:
#                 old_data.update(data)
#             data = old_data
#         except (NotFound, NotAuthorized):
#             return base.abort(404, _(u'Dataset not found'))

#         if data.get(u'state', u'').startswith(u'draft'):
#             g.form_action = h.url_for(u'{}.new'.format(package_type))
#             g.form_style = u'new'

#             return dataset.CreateView().get(
#                 package_type,
#                 data=data,
#                 errors=errors,
#                 error_summary=error_summary
#             )

#         pkg = context.get(u"package")
#         resources_json = h.json.dumps(data.get(u'resources', []))

#         try:
#             logic.check_access(u'package_update', context, {u'id': id})
#         except NotAuthorized:
#             return base.abort(
#                 403,
#                 _(u'User %r not authorized to edit %s') % (g.user, id)
#             )

#         if data and not data.get(u'tag_string'):
#             data[u'tag_string'] = u', '.join(
#                 h.dict_list_reduce(pkg_dict.get(u'tags', {}), u'name')
#             )
#         errors = errors or {}
#         form_snippet = _get_pkg_template(
#             u'package_form', package_type=package_type
#         )
#         form_vars = {
#             u'data': data,
#             u'errors': errors,
#             u'error_summary': error_summary,
#             u'action': u'edit',
#             u'dataset_type': package_type,
#             u'form_style': u'edit'
#         }
#         errors_json = h.json.dumps(errors)

#         g.pkg = pkg
#         g.resources_json = resources_json
#         g.errors_json = errors_json

#         _setup_template_variables(
#             context, {u'id': id}, package_type=package_type
#         )

#         form_vars[u'stage'] = [u'active']
#         if data.get(u'state', u'').startswith(u'draft'):
#             form_vars[u'stage'] = [u'active', u'complete']

#         edit_template = _get_pkg_template(u'edit_template', package_type)
#         return base.render(
#             edit_template,
#             extra_vars={
#                 u'form_vars': form_vars,
#                 u'form_snippet': form_snippet,
#                 u'dataset_type': package_type,
#                 u'pkg_dict': pkg_dict,
#                 u'pkg': pkg,
#                 u'resources_json': resources_json,
#                 u'form_snippet': form_snippet,
#                 u'errors_json': errors_json
#             }
#         )


class ApprovalWorkflowRejectView(MethodView):
    def _prepare(self):
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'auth_user_obj': g.userobj
        }
        return context

    def post(self, package_type, id):
        if u'cancel' in request.form:
            return h.redirect_to(u'{}.edit'.format(package_type), id=id)
        context = self._prepare()
        try:
            pkg = get_action(u'package_show')(context, {u'id': id})
            pkg['state'] = u'draft'
            pkg_dict = get_action(u'package_update')(context, pkg)
        except NotFound:
            return base.abort(404, _(u'Dataset not found'))
        except NotAuthorized:
            return base.abort(
                403,
                _(u'Unauthorized to edit package %s') % u''
            )

        h.flash_notice(_(u'Dataset has been rejected. Saved as Draft'))
        return h.redirect_to(u'dataset.search')

    def get(self, package_type, id):
        context = self._prepare()
        try:
            pkg_dict = get_action(u'package_show')(context, {u'id': id})
        except NotFound:
            return base.abort(404, _(u'Dataset not found'))
        except NotAuthorized:
            return base.abort(
                403,
                _(u'Unauthorized to delete package %s') % u''
            )

        dataset_type = pkg_dict[u'type'] or package_type

        # TODO: remove
        g.pkg_dict = pkg_dict

        return base.render(
            u'package/confirm_reject.html', {
                u'pkg_dict': pkg_dict,
                u'dataset_type': dataset_type
            }
        )


dataset_approval_workflow.add_url_rule(
    u'/edit/<id>', view_func=EditView_.as_view(str(u'edit'))
)
dataset_approval_workflow.add_url_rule(
    u'/reject/<id>', view_func=ApprovalWorkflowRejectView.as_view(str(u'reject'))
)
