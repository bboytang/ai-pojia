"""Load AI Pojia into AstrBot's request-local system prompt."""

from astrbot.api import AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Star

from .astrbot_policy import apply_policy


class AiPojiaPlugin(Star):
    def __init__(self, context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    @filter.on_llm_request(priority=-100000)
    async def on_request(self, event: AstrMessageEvent, req: ProviderRequest):
        if self.config.get("enabled", True) is not True:
            return
        req.system_prompt = apply_policy(
            req.system_prompt or "",
            self.config.get("authorized_execution", True) is True,
        )
