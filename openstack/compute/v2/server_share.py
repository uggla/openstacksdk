# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from openstack import resource


class ShareMapping(resource.Resource):
    resource_key = 'share'
    resources_key = 'shares'
    base_path = '/servers/%(server_id)s/shares'

    # capabilities
    allow_create = True
    allow_fetch = True
    allow_commit = False
    allow_delete = True
    allow_list = True

    _max_microversion = '2.97'

    #: The ID for the server.
    server_id = resource.URI('server_id')
    #: The ID of the share mapping.
    uuid = resource.Body('uuid')
    #: The ID of the share.
    share_id = resource.Body('share_id', default='')
    #: The status of the share.
    status = resource.Body('status')
    #: Tags for the shares.
    tag = resource.Body('tag')
    #: The location of the share.
    export_location = resource.Body('export_location', default='')
