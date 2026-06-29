import pandas as pd
from pydantic import BaseModel, Field
from typing import Literal

from api_ingestion.BaseEndpoint import BaseEndpoint
from .utils import worker


class ConfigTrending(BaseModel):
    is_enabled:  bool                          = Field(False, description="Toggle endpoint enabled / disabled")
    override:    bool                          = Field(False, description="Override endpoint data")
    media_type:  Literal["all", "movie", "tv"] = Field("all", description="Media type to get. Select from: all | movie | tv")
    time_window: Literal["day", "week"]        = Field("week", description="Time window to get. Select from: day | week")


class Trending(BaseEndpoint):
    # Trending movies/serieses/both in selected time period
    path = "trending"
    schema = {'page': int, 'results': list, 'total_pages': int, 'total_results': int}
    output_format = 'csv'
    output_schema = {'adult': bool, 'backdrop_path': str, 'id': "Int64", 'name': str, 'title': str, 'original_name': str, 'original_title': str, 
                     'overview':str, 'poster_path': str, 'media_type': str, 'original_language': str, 'genre_ids': object, 'popularity': float, 
                     'first_air_date': str, 'release_date': str, 'softcore': bool, 'vote_average': float, 'vote_count': "Int64", 'origin_country': object, 'video': bool}

    def __init__(self, client):
        super().__init__(client, cfg_cls=ConfigTrending)
        self.path = f"{self.path.strip()}/{self.cfg_endpoint.media_type}/{self.cfg_endpoint.time_window}"
        
        self.total_pages=client.cfg_client.total_pages
        self.pages_per_batch=client.cfg_client.pages_per_batch
    
    def run(self):
        worker(self)
