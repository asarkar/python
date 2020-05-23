import argparse
import asyncio
import logging
from datetime import datetime
from typing import Dict, List

import aiohttp
import numpy as np
from dateutil.relativedelta import relativedelta


class GitLabClient:
    logging.basicConfig(
        level=logging.INFO
    )
    logger = logging.getLogger("gitlab")

    def __init__(self, base_url: str, private_token: str, session: aiohttp.ClientSession):
        self.base_url = base_url
        self.private_token = private_token
        self.session = session
        self.per_page = 50
        self.datetime_fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
        self.created_after = (datetime.utcnow() - relativedelta(years=1)).strftime(self.datetime_fmt)
        GitLabClient.logger.info("Checking all merge requests created after %s", self.created_after)

    async def get_num_pages(self, group_id: str) -> int:
        resp = await self.session.head(
            f"{self.base_url}/api/v4/groups/{group_id}/merge_requests",
            headers={"PRIVATE-TOKEN": self.private_token},
            params={"state": "merged", "per_page": self.per_page, "created_after": self.created_after}
        )
        resp.raise_for_status()
        num_pages = int(resp.headers["X-Total-Pages"])
        return num_pages

    async def get_mrs(self, group_id: str, page_num: int) -> List[Dict[str, object]]:
        resp = await self.session.get(
            f"{self.base_url}/api/v4/groups/{group_id}/merge_requests",
            headers={"PRIVATE-TOKEN": self.private_token},
            params={"state": "merged", "view": "simple", "per_page": self.per_page, "page": page_num,
                    "created_after": self.created_after}
        )
        resp.raise_for_status()
        body = await resp.json()
        return body

    async def get_mr_ages(self, group_id: str, page_num: int) -> List[float]:
        def age(merge_request: Dict[str, object]) -> float:
            created = datetime.strptime(merge_request["created_at"], self.datetime_fmt)
            updated = datetime.strptime(merge_request["updated_at"], self.datetime_fmt)
            diff = updated - created
            return diff.days * 1440 + diff.seconds / 60

        GitLabClient.logger.debug("Fetching MRs from %s to %s", ((page_num - 1) * self.per_page + 1),
                                  page_num * self.per_page)
        mrs = await self.get_mrs(group_id, page_num)
        return [age(mr) for mr in mrs]

    @staticmethod
    async def main():
        parser = argparse.ArgumentParser()
        parser.add_argument("-u", "--url")
        parser.add_argument("-t", "--token")
        parser.add_argument("-g", "--gid", type=int)
        args = parser.parse_args()
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            client = GitLabClient(args.url, args.token, session)
            num_pages = await client.get_num_pages(args.gid)
            GitLabClient.logger.debug("There are %s pages", num_pages)
            nested_ages = await asyncio.gather(
                *(client.get_mr_ages(args.gid, page) for page in range(1, num_pages + 1))
            )
            arr = np.array([age for ages in nested_ages for age in ages])
            ninety_ninth_percentile = np.percentile(arr, 99) // (60 * 24)
            GitLabClient.logger.info(f"99% of total {arr.size} MRs took {ninety_ninth_percentile:4.2f} days to close")


asyncio.run(GitLabClient.main())
