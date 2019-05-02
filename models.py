# For more details, see
# http://docs.sqlalchemy.org/en/latest/orm/tutorial.html#declare-a-mapping
from anthill.framework.db import db
from anthill.framework.utils import timezone
from anthill.framework.utils.module_loading import import_string
from anthill.framework.utils.functional import cached_property
from anthill.framework.utils.translation import translate_lazy as _
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils.types import JSONType, ChoiceType
from bot.actions.base import BaseAction
from typing import List


bot_action_association = db.Table(
    'bot_action_association', db.metadata,
    db.Column('bot_id', db.ForeignKey('bots.id'), primary_key=True),
    db.Column('action_id', db.ForeignKey('actions.id'), primary_key=True)
)


class Bot(db.Model):
    """
    Automation format:
    {
        "connect": [
            {
                "group": "name_1"
            },
            {
                "group": "name_2"
            },
            ...
            {
                "group": "name_N"
            }
        ]
    }
    """
    __tablename__ = 'bots'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    description = db.Column(db.String(512), nullable=False)
    payload = db.Column(JSONType, nullable=False, default={})
    automation = db.Column(JSONType, nullable=False, default={})
    last_login = db.Column(db.DateTime, nullable=True, default=None)
    created = db.Column(db.DateTime, default=timezone.now)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    actions = db.relationship(
        'Action', secondary=bot_action_association, backref='bots', lazy='dynamic')

    @property
    def connect_groups(self) -> List[str]:
        return [item['group'] for item in self.automation['connect']]

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Bot(name=%s, description=%s)>" % (self.name, self.description)

    @hybrid_property
    def photo(self):
        return self.payload.get('avatar')

    @hybrid_property
    def first_name(self):
        return self.payload.get('first_name')

    @hybrid_property
    def last_name(self):
        return self.payload.get('last_name')


class Action(db.Model):
    __tablename__ = 'actions'

    TYPES = (
        ('path', _('Path')),
        ('code', _('Code')),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(512), nullable=False)
    value = db.Column(db.Text, nullable=False)
    type = db.Column(ChoiceType(TYPES))
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    formatter_id = db.Column(db.Integer, db.ForeignKey('formatters.id'))

    def __repr__(self):
        return "<Action(name=%s, description=%s)>" % (self.name, self.description)

    def __getattr__(self, item):
        return getattr(self.value_object, item)

    @cached_property
    def value_object(self) -> BaseAction:
        return import_string(self.value)()


class ResultFormatter(db.Model):
    __tablename__ = 'formatters'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    template = db.Column(db.Text, nullable=False)
    action = db.relationship('Action', backref='formatter', lazy='dynamic')
    enabled = db.Column(db.Boolean, nullable=False, default=True)
