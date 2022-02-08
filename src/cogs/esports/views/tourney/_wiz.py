from __future__ import annotations

from ...views.base import EsportsBaseView

from core import Context


class TourneySetupWizard(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx)

        self.ctx = ctx
        self.record = None
