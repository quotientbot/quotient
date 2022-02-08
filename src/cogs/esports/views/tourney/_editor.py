from __future__ import annotations

from ...views.base import EsportsBaseView
import discord
from models import Tourney
from ._buttons import *


class TourneyEditor(EsportsBaseView):
    record: Tourney

    def __init__(self):
        super().__init__(timeout=100, name="Tourney Editor")
