import sys
from pydantic import BaseModel, Field

ROOT_DIRNAME = "DataEngProj"
ROOT_PATH = __file__.split(ROOT_DIRNAME, 1)[0] + ROOT_DIRNAME
sys.path.append(ROOT_PATH)

from api_ingestion.BaseClient import BaseClient


class ConfigTMDB(BaseModel):
    override:        bool = Field(False, description="Override existing client data")
    total_pages:     int  = Field(0, description="Page limit to fetch (0=No limit)")
    pages_per_batch: int  = Field(10, description="Num of concurrent pages processed in one file")
    endpoints:       dict = Field({}, description="Param dict for each endpoint")


class TMDB(BaseClient):
    base_url: str              = "https://api.themoviedb.org/3"
    api_key: str               = "af3c279892381d31b47f4c83c755c52c"
    api_read_access_token: str = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJhZjNjMjc5ODkyMzgxZDMxYjQ3ZjRjODNjNzU1YzUyYyIsIm5iZiI6MTc4MTc4MDgwNS40MTYsInN1YiI6IjZhMzNkMTQ1OGYzYTkwZWY1M2MyZWIyZCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.otysWCQP3AVl01jNuflVvbr0YBDUbYr97EGLRsrCqpE"
    
    def __init__(self):
        default_headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_read_access_token}"
            }
        super().__init__(default_headers, cfg_cls=ConfigTMDB)
        self.endpoints = self.get_active_endpoints("Endpoints", self.cfg_client.endpoints)
    
    def run(self):
        self.logger.title("Start API Client: 'TMDB'")

        for ep_name, ep_handler in self.endpoints.items():
            self.logger.subtitle(f"Start endpoint: '{ep_name}'")
            ep_handler.run()
            self.logger.subtitle(f"End endpoint: '{ep_name}'")

if __name__ == "__main__":
    TMDB().run()
