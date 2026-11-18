from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


EngineName = Literal["auto", "yt-dlp", "gallery-dl"]


class CreateTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=8, max_length=4096)
    engine: EngineName = "auto"
