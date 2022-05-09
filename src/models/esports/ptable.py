from tortoise import fields, models

from models.helpers import *


class PtableTourney(models.Model):
    class Meta:
        table = "ptable_tourney"

    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField()
    associative_id = fields.CharField(max_length=10)
    title = fields.CharField(max_length=100)
    secondary_title = fields.CharField(max_length=100)
    footer = fields.CharField(max_length=100)

    per_kill = fields.IntField(default=0)
    postion_pts = fields.JSONField(default=dict)

    background_image = fields.CharField(max_length=200)
    colors = fields.JSONField(default=dict)

    created_at = fields.DatetimeField(auto_now_add=True)
    teams: fields.ManyToManyRelation["PtableTeam"] = fields.ManyToManyField("models.PtableTeam")
    matches: fields.ManyToManyRelation["PtableMatch"] = fields.ManyToManyField("models.PtableMatch")


class PtableTeam(models.Model):
    class Meta:
        table = "ptable_teams"

    id = fields.IntField(pk=True)
    team_name = fields.CharField(max_length=100)
    email = fields.CharField(max_length=100, null=True)
    phone = fields.CharField(max_length=10, null=True)
    logo = fields.CharField(max_length=200, null=True)
    added_by = fields.BigIntField()
    team_owner = fields.BigIntField()
    players = ArrayField(fields.BigIntField(default=list))
    last_used = fields.DatetimeField(auto_now=True)


class PtableMatch(models.Model):
    class Meta:
        table = "ptable_match"

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    created_at = fields.DatetimeField(auto_now=True)
    created_by = fields.BigIntField()
    results = fields.JSONField()
