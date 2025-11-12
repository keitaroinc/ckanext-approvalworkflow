import datetime
import json
from six import text_type
import sqlalchemy as sa
from sqlalchemy.orm import class_mapper
try:
    from sqlalchemy.engine import Row
except ImportError:
    try:
        from sqlalchemy.engine.result import RowProxy as Row
    except ImportError:
        from sqlalchemy.engine.base import RowProxy as Row

from ckan import model
import ckan.model.meta as meta
from ckan.model.types import make_uuid
from sqlalchemy.orm import relationship
from ckan.model.domain_object import DomainObject

metadata = sa.MetaData()

approval_workflow_table = None
approval_workflow_organization_table = None
approval_workflow_dataset_table = None

types = sa.types

approval_workflow_table = sa.Table(
    'ckanext_approvalworkflow', model.meta.metadata,
    sa.Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
    sa.Column('active', types.Boolean, default=False),
    sa.Column('approval_workflow_active', types.UnicodeText),
    sa.Column('active_per_organization', types.Boolean, default=False),
    sa.Column('deactivate_edit', types.Boolean, default=False),
    sa.Column('created', types.DateTime, default=datetime.datetime.utcnow),
    sa.Column('modified', types.DateTime, default=datetime.datetime.utcnow),
    sa.Column('extras', types.UnicodeText, default=u'{}'),
    extend_existing=True
    )

approval_workflow_organization_table = sa.Table(
    'ckanext_approvalworkflow_organization', model.meta.metadata,
    sa.Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
    sa.Column('approvalworkflow_id', sa.ForeignKey('ckanext_approvalworkflow.id')),
    sa.Column('organization_id', types.UnicodeText, default=u'{}'),
    sa.Column('active', types.Boolean, default=False),
    sa.Column('deactivate_edit', types.Boolean, default=False),
    sa.Column('org_approval_workflow_active', types.UnicodeText, default=u'{}'),
    sa.Column('created', types.DateTime, default=datetime.datetime.utcnow),
    sa.Column('modified', types.DateTime, default=datetime.datetime.utcnow),
    sa.Column('extras', types.UnicodeText, default=u'{}'),
    extend_existing=True
    )

approval_workflow_dataset_table = sa.Table(
    'ckanext_approvalworkflow_dataset', model.meta.metadata,
    sa.Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
    sa.Column('package_id', types.UnicodeText, default=False),
    sa.Column('user_name', types.UnicodeText, default=False),
    sa.Column('timestamp', types.DateTime, default=datetime.datetime.utcnow),
    sa.Column('approval_notes', types.UnicodeText, default=u'{}'),
    sa.Column('approval_extras', types.UnicodeText, default=u'{}'),
    extend_existing=True
    )


class ApprovalWorkflow(DomainObject):
    def __init__(self, **kwargs):
        self.id = make_uuid()

    @classmethod
    def get(cls, **kw):
        '''Finds a single entity in the register.'''
        query = model.Session.query(cls).autoflush(False)
        return query.filter_by(**kw).first()

    @classmethod
    def approval_workflow(cls, **kw):
        '''Finds a single entity in the register.'''

        query = model.Session.query(cls).autoflush(False)
        query = query.filter_by(**kw)
        if approval_workflow:
            query = query.order_by(sa.cast(cls.approval_workflow, sa.Integer)).filter(cls.approval_workflow != '')
        else:
            query = query.order_by(cls.created.desc())
        return query.all()


class ApprovalWorkflowOrganization(DomainObject):
    def __init__(self, **kwargs):
        self.id=make_uuid()

    @classmethod
    def get(cls, **kw):
        '''Finds a single entity in the register.'''
        query = model.Session.query(cls).autoflush(False)
        return query.filter_by(**kw).first()

    @classmethod
    def approval_workflow_organization(cls, **kw):
        '''Finds a single entity in the register.'''
        query = model.Session.query(cls).autoflush(False)
        query = query.filter_by(**kw)
        return query.all()


class ApprovalWorkflowDataset(DomainObject):

    def __init__(self, **kwargs):
        self.id = make_uuid()


meta.mapper(ApprovalWorkflow, approval_workflow_table, properties={})
meta.mapper(ApprovalWorkflowDataset, approval_workflow_dataset_table, properties={})
meta.mapper(
    ApprovalWorkflowOrganization,
    approval_workflow_organization_table, properties={'approval_workflow_id': relationship (ApprovalWorkflow)}
)


def table_dictize(obj, context, **kw):
    '''Get any model object and represent it as a dict'''
    result_dict = {}

    if isinstance(obj, Row):
        fields = obj.keys()
    else:
        ModelClass = obj.__class__
        table = class_mapper(ModelClass).mapped_table
        fields = [field.name for field in table.c]

    for field in fields:
        name = field
        value = getattr(obj, name)
        if name == 'extras' and value:
            result_dict.update(json.loads(value))
        elif value is None:
            result_dict[name] = value
        elif isinstance(value, dict):
            result_dict[name] = value
        elif isinstance(value, int):
            result_dict[name] = value
        elif isinstance(value, datetime.datetime):
            result_dict[name] = value.isoformat()
        elif isinstance(value, list):
            result_dict[name] = value
        else:
            result_dict[name] = text_type(value)

    result_dict.update(kw)

    context['metadata_modified'] = max(result_dict.get('revision_timestamp', ''),
                                       context.get('metadata_modified', ''))

    return result_dict


def init_db():
    engine = model.Session.bind or model.meta.engine
    approval_workflow_table.create(engine, checkfirst=True)
    approval_workflow_organization_table.create(engine, checkfirst=True)
    approval_workflow_dataset_table.create(engine, checkfirst=True)


def drop_db():
    engine = model.Session.bind or model.meta.engine
    approval_workflow_organization_table.drop(engine, checkfirst=True)
    approval_workflow_table.drop(engine, checkfirst=True)
    approval_workflow_dataset_table.drop(engine, checkfirst=True)
