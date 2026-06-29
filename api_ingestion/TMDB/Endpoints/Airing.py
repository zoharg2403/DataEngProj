import pandas as pd
from pydantic import BaseModel, Field

from api_ingestion.BaseEndpoint import BaseEndpoint
from .utils import worker


class ConfigAiring(BaseModel):
    is_enabled: bool = Field(False, description="Toggle endpoint enabled / disabled")
    override:   bool = Field(False, description="Override endpoint data")


class Airing(BaseEndpoint):
    # Currently Airing (On the Air) serieses
    path = "tv/on_the_air"
    schema = {'page': int, 'results': list, 'total_pages': int, 'total_results': int}
    output_format = 'csv'
    output_schema = {'adult': bool, 'backdrop_path':str, 'genre_ids': object, 'id': "Int64", 'origin_country': object,'original_language': str, 'original_name': str, 
                     'overview': str, 'popularity': float,'poster_path':str , 'first_air_date': str, 'softcore': bool, 'name': str, 'vote_average': float, 'vote_count': "Int64"}

    def __init__(self, client):
        super().__init__(client, cfg_cls=ConfigAiring)

        self.total_pages = client.cfg_client.total_pages
        self.pages_per_batch = client.cfg_client.pages_per_batch
    
    def run(self):
        worker(self)


    
