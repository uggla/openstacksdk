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

from openstack.shared_file_system.v2 import resource_locks as _resource_locks
from openstack.tests.functional.shared_file_system import base


class ResourceLocksTest(base.BaseSharedFileSystemTest):
    def setUp(self):
        super(ResourceLocksTest, self).setUp()

        self.SHARE_NAME = self.getUniqueString()
        share = self.user_cloud.shared_file_system.create_share(
            name=self.SHARE_NAME,
            size=2,
            share_type="dhss_false",
            share_protocol='NFS',
            description=None,
        )
        self.user_cloud.shared_file_system.wait_for_status(
            share,
            status='available',
            failures=['error'],
            interval=5,
            wait=self._wait_for_timeout,
        )
        self.assertIsNotNone(share)
        self.assertIsNotNone(share.id)
        self.SHARE_ID = share.id
        lock = self.create_resource_lock(
            resource_action='delete',
            resource_type='share',
            resource_id=self.SHARE_ID,
            lock_reason='openstacksdk testing',
        )
        self.LOCK_ID = lock.id

    def test_get(self):
        lock = self.user_cloud.shared_file_system.get_resource_lock(
            self.LOCK_ID
        )
        assert isinstance(lock, _resource_locks.ResourceLock)
        self.assertEqual(self.LOCK_ID, lock.id)

    def test_list(self):
        resource_locks = self.user_cloud.share.resource_locks()
        self.assertGreater(len(list(resource_locks)), 0)
        lock_attrs = (
            'id',
            'lock_reason',
            'resource_type',
            'resource_action',
            'lock_context',
            'created_at',
            'updated_at',
        )
        for lock in resource_locks:
            for attribute in lock_attrs:
                self.assertTrue(hasattr(lock, attribute))
