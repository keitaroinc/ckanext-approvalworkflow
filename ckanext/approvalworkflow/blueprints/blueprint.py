from flask.views import MethodView
import json
import logging
import ckan.lib.base as base
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.uploader as uploader
import ckan.logic as logic
import ckan.model as model
import ckan.plugins as plugins
from ckan.common import _, g, request
from ckan.lib.search import SearchIndexError
from ckan.views.dataset import (
    _get_package_type
)
import ckan.lib.navl.dictization_functions
from ckan.common import config, asbool
import ckan.authz as authz
import ckan.lib.search as search


NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key

log = logging.getLogger(__name__)


def approval_workflow_settings():
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'auth_user_obj': g.userobj,
        u'for_view': True
    }
    # turn on approval workflow
    # who can review a dataset? org admin sysadmin
    # which organizations need approval workflow


_check_access = logic.check_access
_validate = ckan.lib.navl.dictization_functions.validate


# def package_review_search(context, data_dict):
#     schema = (context.get('schema') or
#               logic.schema.default_package_search_schema())
#     data_dict, errors = _validate(data_dict, schema, context)
#     # put the extras back into the data_dict so that the search can
#     # report needless parameters
#     data_dict.update(data_dict.get('__extras', {}))
#     data_dict.pop('__extras', None)
#     if errors:
#         raise ValidationError(errors)

#     model = context['model']
#     session = context['session']
#     user = context.get('user')

#     _check_access('package_search', context, data_dict)

#     # Move ext_ params to extras and remove them from the root of the search
#     # params, so they don't cause and error
#     data_dict['extras'] = data_dict.get('extras', {})
#     for key in [key for key in data_dict.keys() if key.startswith('ext_')]:
#         data_dict['extras'][key] = data_dict.pop(key)

#     # set default search field
#     data_dict['df'] = 'text'

#     # check if some extension needs to modify the search params
#     for item in plugins.PluginImplementations(plugins.IPackageController):
#         data_dict = item.before_search(data_dict)

#     # the extension may have decided that it is not necessary to perform
#     # the query
#     abort = data_dict.get('abort_search', False)

#     if data_dict.get('sort') in (None, 'rank'):
#         data_dict['sort'] = config.get('ckan.search.default_package_sort') or 'score desc, metadata_modified desc'

#     results = []
#     if not abort:
#         if asbool(data_dict.get('use_default_schema')):
#             data_source = 'data_dict'
#         else:
#             data_source = 'validated_data_dict'
#         data_dict.pop('use_default_schema', None)

#         result_fl = data_dict.get('fl')
#         if not result_fl:
#             data_dict['fl'] = 'id {0}'.format(data_source)
#         else:
#             data_dict['fl'] = ' '.join(result_fl)

#         # Remove before these hit solr FIXME: whitelist instead
#         include_private = asbool(data_dict.pop('include_private', False))
#         include_drafts = asbool(data_dict.pop('include_drafts', False))
#         include_review = asbool(data_dict.pop('include_review', False))

#         data_dict.setdefault('fq', '')
#         if not include_private:
#             data_dict['fq'] = '+capacity:public ' + data_dict['fq']
#         if include_drafts:
#             data_dict['fq'] += ' +state:(active OR draft)'
#         if include_review:
#             data_dict['fq'] += ' +state:(pending)'

#         # Pop these ones as Solr does not need them
#         extras = data_dict.pop('extras', None)

#         # enforce permission filter based on user
#         if context.get('ignore_auth') or (user and authz.is_sysadmin(user)):
#             labels = None
#         else:
#             labels = lib_plugins.get_permission_labels(
#                 ).get_user_dataset_labels(context['auth_user_obj'])

#         query = search.query_for(model.Package)
#         query.run(data_dict, permission_labels=labels)
#         print(query.results)

#         # Add them back so extensions can use them on after_search
#         data_dict['extras'] = extras

#         if result_fl:
#             for package in query.results:
#                 if isinstance(package, text_type):
#                     package = {result_fl[0]: package}
#                 extras = package.pop('extras', {})
#                 package.update(extras)
#                 results.append(package)
#         else:
#             for package in query.results:
#                 # get the package object
#                 package_dict = package.get(data_source)
#                 # use data in search index if there
#                 if package_dict:
#                     # the package_dict still needs translating when being viewed
#                     package_dict = json.loads(package_dict)
#                     if context.get('for_view'):
#                         for item in plugins.PluginImplementations(
#                                 plugins.IPackageController):
#                             package_dict = item.before_view(package_dict)
#                     results.append(package_dict)
#                 else:
#                     log.error('No package_dict is coming from solr for package '
#                               'id %s', package['id'])

#         count = query.count
#         facets = query.facets
#     else:
#         count = 0
#         facets = {}
#         results = []

#     search_results = {
#         'count': count,
#         'facets': facets,
#         'results': results,
#         'sort': data_dict['sort']
#     }

#     # create a lookup table of group name to title for all the groups and
#     # organizations in the current search's facets.
#     group_names = []
#     for field_name in ('groups', 'organization'):
#         group_names.extend(facets.get(field_name, {}).keys())

#     groups = (session.query(model.Group.name, model.Group.title)
#                     .filter(model.Group.name.in_(group_names))
#                     .all()
#               if group_names else [])
#     group_titles_by_name = dict(groups)

#     # Transform facets into a more useful data structure.
#     restructured_facets = {}
#     for key, value in facets.items():
#         restructured_facets[key] = {
#             'title': key,
#             'items': []
#         }
#         for key_, value_ in value.items():
#             new_facet_dict = {}
#             new_facet_dict['name'] = key_
#             if key in ('groups', 'organization'):
#                 display_name = group_titles_by_name.get(key_, key_)
#                 display_name = display_name if display_name and display_name.strip() else key_
#                 new_facet_dict['display_name'] = display_name
#             elif key == 'license_id':
#                 license = model.Package.get_license_register().get(key_)
#                 if license:
#                     new_facet_dict['display_name'] = license.title
#                 else:
#                     new_facet_dict['display_name'] = key_
#             else:
#                 new_facet_dict['display_name'] = key_
#             new_facet_dict['count'] = value_
#             restructured_facets[key]['items'].append(new_facet_dict)
#     search_results['search_facets'] = restructured_facets

#     # check if some extension needs to modify the search results
#     for item in plugins.PluginImplementations(plugins.IPackageController):
#         search_results = item.after_search(search_results, data_dict)

#     # After extensions have had a chance to modify the facets, sort them by
#     # display name.
#     for facet in search_results['search_facets']:
#         search_results['search_facets'][facet]['items'] = sorted(
#             search_results['search_facets'][facet]['items'],
#             key=lambda facet: facet['display_name'], reverse=True)

#     return search_results


# def approve_dataset_metadata(context, data_dict):
#     '''Update a dataset (package).

#     You must be authorized to edit the dataset and the groups that it belongs
#     to.

#     .. note:: Update methods may delete parameters not explicitly provided in the
#         data_dict. If you want to edit only a specific attribute use `package_patch`
#         instead.

#     It is recommended to call
#     :py:func:`ckan.logic.action.get.package_show`, make the desired changes to
#     the result, and then call ``package_update()`` with it.

#     Plugins may change the parameters of this function depending on the value
#     of the dataset's ``type`` attribute, see the
#     :py:class:`~ckan.plugins.interfaces.IDatasetForm` plugin interface.

#     For further parameters see
#     :py:func:`~ckan.logic.action.create.package_create`.

#     :param id: the name or id of the dataset to update
#     :type id: string

#     :returns: the updated dataset (if ``'return_package_dict'`` is ``True`` in
#               the context, which is the default. Otherwise returns just the
#               dataset id)
#     :rtype: dictionary

#     '''
#     model = context['model']
#     session = context['session']
#     name_or_id = data_dict.get('id') or data_dict.get('name')

#     if name_or_id is None:
#         raise ValidationError({'id': _('Missing value')})

#     pkg = model.Package.get(name_or_id)
#     if pkg is None:
#         raise NotFound(_('Package was not found.'))
#     context["package"] = pkg

#     # immutable fields
#     data_dict["id"] = pkg.id
#     data_dict['type'] = pkg.type

#     _check_access('package_update', context, data_dict)

#     user = context['user']
#     # get the schema
#     package_plugin = lib_plugins.lookup_package_plugin(pkg.type)
#     if 'schema' in context:
#         schema = context['schema']
#     else:
#         schema = package_plugin.update_package_schema()

#     if 'api_version' not in context:
#         # check_data_dict() is deprecated. If the package_plugin has a
#         # check_data_dict() we'll call it, if it doesn't have the method we'll
#         # do nothing.
#         check_data_dict = getattr(package_plugin, 'check_data_dict', None)
#         if check_data_dict:
#             try:
#                 package_plugin.check_data_dict(data_dict, schema)
#             except TypeError:
#                 # Old plugins do not support passing the schema so we need
#                 # to ensure they still work.
#                 package_plugin.check_data_dict(data_dict)

#     resource_uploads = []
#     for resource in data_dict.get('resources', []):
#         # file uploads/clearing
#         upload = uploader.get_resource_uploader(resource)

#         if 'mimetype' not in resource:
#             if hasattr(upload, 'mimetype'):
#                 resource['mimetype'] = upload.mimetype

#         if 'size' not in resource and 'url_type' in resource:
#             if hasattr(upload, 'filesize'):
#                 resource['size'] = upload.filesize

#         resource_uploads.append(upload)

#     data, errors = lib_plugins.plugin_validate(
#         package_plugin, context, data_dict, schema, 'package_update')
#     log.debug('package_update validate_errs=%r user=%s package=%s data=%r',
#               errors, context.get('user'),
#               context.get('package').name if context.get('package') else '',
#               data)

#     if errors:
#         model.Session.rollback()
#         raise ValidationError(errors)

#     # avoid revisioning by updating directly
#     model.Session.query(model.Package).filter_by(id=pkg.id).update(
#         {"metadata_modified": datetime.datetime.utcnow(), "status": "active"})
#     model.Session.refresh(pkg)

#     pkg = model_save.package_dict_save(data, context)

#     context_org_update = context.copy()
#     context_org_update['ignore_auth'] = True
#     context_org_update['defer_commit'] = True
#     _get_action('package_owner_org_update')(context_org_update,
#                                             {'id': pkg.id,
#                                              'organization_id': pkg.owner_org})

#     # Needed to let extensions know the new resources ids
#     model.Session.flush()
#     for index, (resource, upload) in enumerate(
#             zip(data.get('resources', []), resource_uploads)):
#         resource['id'] = pkg.resources[index].id

#         upload.upload(resource['id'], uploader.get_max_resource_size())

#     for item in plugins.PluginImplementations(plugins.IPackageController):
#         item.edit(pkg)

#         item.after_update(context, data)

#     # Create activity
#     if not pkg.private:
#         user_obj = model.User.by_name(user)
#         if user_obj:
#             user_id = user_obj.id
#         else:
#             user_id = 'not logged in'
#         activity = pkg.activity_stream_item('changed', user_id)
#         session.add(activity)

#     if not context.get('defer_commit'):
#         model.repo.commit()

#     log.debug('Updated object %s' % pkg.name)

#     return_id_only = context.get('return_id_only', False)

#     # Make sure that a user provided schema is not used on package_show
#     context.pop('schema', None)

#     # we could update the dataset so we should still be able to read it.
#     context['ignore_auth'] = True
#     output = data_dict['id'] if return_id_only \
#             else _get_action('package_show')(context, {'id': data_dict['id']})

#     return output


class ApprovalEditView(MethodView):
    def _prepare(self, id, data=None):
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'auth_user_obj': g.userobj,
            u'save': u'save' in request.form
        }
        return context

    def post(self, package_type, id):
        context = self._prepare(id)
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
                    data_dict[u'tags'] = ckan.views.dataset._tag_string_to_list(
                        data_dict[u'tag_string']
                    )
                del data_dict[u'_ckan_phase']
                del data_dict[u'save']
            context[u'message'] = data_dict.get(u'log_message', u'')
            data_dict['id'] = id
            data_dict['state'] = 'active'
            pkg_dict = get_action(u'package_update')(context, data_dict)

            return ckan.views.dataset._form_save_redirect(
                pkg_dict[u'name'], u'edit', package_type=package_type
            )
        except NotAuthorized:
            return base.abort(403, _(u'Unauthorized to read package %s') % id)
        except NotFound:
            return base.abort(404, _(u'Dataset not found'))
        except SearchIndexError as e:
            try:
                exc_str = text_type(repr(e.args))
            except Exception:  # We don't like bare excepts
                exc_str = text_type(str(e))
            return base.abort(
                500,
                _(u'Unable to update search index.') + exc_str
            )
        except ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(package_type, id, data_dict, errors, error_summary)


# def register_dataset_plugin_rules(blueprint):
#     blueprint.add_url_rule(
#          u'/edit/<id>', view_func=ApprovalEditView.as_view(str(u'edit')))

# register_dataset_plugin_rules(dataset_blueprint)
# register_approval_plugin_rules(blueprint_edit)
