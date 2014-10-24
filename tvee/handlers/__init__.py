#!/usr/bin/env python
# coding=utf-8

import json

from tornado.web import RequestHandler, HTTPError


class BaseHandler(RequestHandler):

    @property
    def body_arguments(self):
        return json.loads(self.request.body.decode('utf-8'))

    @property
    def list_query(self):
        query = self.model.select()
        page = self.get_argument('page', None)
        if page:
            page = int(page)
            if page < 1:
                raise HTTPError(400)
            query = query.paginate(page)
        return query

    def delete_by_id(self, id):
        object = self.model.get_with_validate(self.model.id == id)
        object.delete_instance(recursive=True)
        self.finish_with_status(200)

    def finish_with_json(self, json_value):
        self.finish(json.dumps(json_value))

    def finish_with_status(self, status):
        self.set_status(status)
        self.finish({'status': status})


from .api import *
from .frontend import *
