#!/usr/bin/env python3

import math
import sys
from location import *
import config
from contime import *
from grid_page import *
import db_fetch

class PageBuilder:
    def __init__(self, bucket):
        self.day = bucket.day
        self.time_range = bucket.time_range
        self.sessions = bucket.items
        self.page = None
        # A PageBucket knows which level it holds: None when the sessions
        # for every level share one page, a Level when they don't.
        self.level = bucket.level

    def make_page(self, page_number, timestr):
        self.page = GridPage(self.day, self.time_range, self.sessions, 
                             page_number, timestr, level=self.level)
        self.page.write()
        self.page.open()


class GridMaker:
    def __init__(self, large_format=False):
        self.contents = None
        self.db = db_fetch.Database("config/schedule.json")
        self.large_format = large_format

    def prep_data(self, contents):
        ''' Sort the sessions into the given time buckets, one bucket per
        slice of each day. Returns the filled container.
        '''
        for session in self.db.get_session_data():
            if session.is_included_in_grid():
                session.get_location().set_used(True)
                contents.add_item(session)
        return contents

    def write_pages(self, contents, page_number):
        for page_bucket in contents.get_buckets():
            if not page_bucket.is_empty():
                builder = PageBuilder(page_bucket)
                builder.make_page(page_number, self.db.get_data_timestamp())
                page_number += 1
        return page_number

    def make_grids(self):
        ''' The default grids put every level on one page per time slice, so
        they need the sessions bucketed by time alone. The large-format grids
        give each level its own page, which needs a separate bucketing by
        level as well as by time.
        '''
        page_number = 1
        self.contents = self.prep_data(PageBucketArray())
        page_number = self.write_pages(self.contents, page_number)

        if self.large_format:
            by_level = self.prep_data(bucket.LevelBucketArray(PageBucketArray))
            page_number = self.write_pages(by_level, page_number)

        print("Done!")

if __name__ == "__main__":
    large_format = "--large-format" in sys.argv
    my_grid_maker = GridMaker(large_format=large_format)
    my_grid_maker.make_grids()

