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

from openstack import _log
from openstack.compute.v2 import server as server_
from openstack.compute.v2 import server_share as server_share_
from openstack.shared_file_system.v2 import share as share_
from openstack.tests.functional.compute import base as ft_base
from openstack import utils


LOG = _log.setup_logging(__name__)


class TestServerShare(ft_base.BaseComputeTest):
    """This test allows testing the functionality through the Shares API
    which enables associating an instance with a share from Manila.
    This test uses a particular Zuul job to meet the prerequisites for
    using this feature. The job will install Devstack:
    1- With the Jammy distribution which contains the appropriate versions
       of Qemu and libvirt.
    2- Install the Manila and Nova services.
    3- Enable the file-backed memory.
    4- Create a test instance and then stop it.

    The association between this test and the job is done through the
    compute_shared_file_system directory which contains this test.
    """

    def setUp(self):
        super().setUp()

        if not self.user_cloud.has_service('shared-file-system'):
            self.skipTest('shared-file-system service not supported by cloud')

        self.server_name = self.getUniqueString()
        self.share_name = self.getUniqueString()

        # create the server and share

        server = self.user_cloud.compute.create_server(
            name=self.server_name,
            flavor_id=self.flavor.id,
            image_id=self.image.id,
            networks='none',
        )
        self.user_cloud.compute.wait_for_server(
            server,
            wait=self._wait_for_timeout,
        )
        self.assertIsInstance(server, server_.Server)
        self.assertEqual(self.server_name, server.name)

        protocol_supported = [
            protocol.capabilities["storage_protocol"]
            for protocol in self.operator_cloud.share.storage_pools()
        ].pop()

        share = self.user_cloud.share.create_share(
            name=self.share_name,
            size=1,
            share_type="dhss_false",
            share_protocol=protocol_supported,
            description=None,
        )
        self.user_cloud.share.wait_for_status(
            share,
            status='available',
            wait=self._wait_for_timeout,
        )
        self.assertIsInstance(share, share_.Share)
        self.assertEqual(self.share_name, share.name)

        self.server = server
        self.share = share

    def tearDown(self):
        self.user_cloud.compute.delete_server(self.server.id)
        self.user_cloud.compute.wait_for_delete(
            self.server,
            wait=self._wait_for_timeout,
        )

        self.user_cloud.share.delete_share(self.share.id)
        self.user_cloud.share.wait_for_delete(
            self.share,
            wait=self._wait_for_timeout,
        )

        super().tearDown()

    def test_server_share(self):
        # Stop server
        self.user_cloud.compute.stop_server(self.server.id)
        self.user_cloud.compute.wait_for_server(
            self.server,
            status='SHUTOFF',
            wait=self._wait_for_timeout,
        )

        # Create the server attachment
        server_share = self.user_cloud.compute.create_share_attachment(
            self.server.id,
            self.share.id,
        )
        self.assertIsInstance(
            server_share,
            server_share_.ShareMapping,
        )

        # List all attached server shares (there should only be one)
        for count in utils.iterate_timeout(
            self._wait_for_timeout,
            message="Wait share attachement to be ready",
        ):
            server_shares = list(
                self.user_cloud.compute.share_attachments(self.server)
            )
            self.assertEqual(1, len(server_shares))
            self.assertIsInstance(
                server_shares[0],
                server_share_.ShareMapping,
            )

            if server_shares[0].status == 'inactive':
                break

        self.assertEqual(server_shares[0].status, 'inactive')

        # Retrieve details of the server share
        server_share = self.user_cloud.compute.get_share_attachment(
            self.server,
            self.share.id,
        )
        self.assertIsInstance(
            server_share,
            server_share_.ShareMapping,
        )
        LOG.debug(server_share)
        self.assertEqual(server_share.status, 'inactive')

        # Delete the server share
        result = self.user_cloud.compute.delete_share_attachment(
            self.server,
            self.share.id,
        )
        self.assertIsNone(result)
        for count in utils.iterate_timeout(
            self._wait_for_timeout, message="Wait proper deletion of the share"
        ):
            server_shares = list(
                self.user_cloud.compute.share_attachments(self.server)
            )
            if len(server_shares) == 0:
                break

        self.assertEqual(0, len(server_shares))

        # Create the server share with a tag
        server_share = self.user_cloud.compute.create_share_attachment(
            self.server.id, self.share.id, tag='mytag'
        )
        self.assertIsInstance(
            server_share,
            server_share_.ShareMapping,
        )

        # Retrieve details of the server share and check tag
        for count in utils.iterate_timeout(
            self._wait_for_timeout,
            message="Wait share attachement to be ready",
        ):
            server_shares = list(
                self.user_cloud.compute.share_attachments(self.server)
            )
            self.assertEqual(1, len(server_shares))
            self.assertIsInstance(
                server_shares[0],
                server_share_.ShareMapping,
            )

            if server_shares[0].status == 'inactive':
                break

        LOG.debug(server_share)
        self.assertEqual(server_shares[0].status, 'inactive')
        self.assertEqual(server_shares[0].tag, 'mytag')

        # Start server
        self.user_cloud.compute.start_server(self.server.id)
        self.user_cloud.compute.wait_for_server(
            self.server,
            status='ACTIVE',
            wait=self._wait_for_timeout,
        )

        # Retrieve details of the server share after power on
        for count in utils.iterate_timeout(
            self._wait_for_timeout,
            message="Wait share attachement to be ready",
        ):
            server_shares = list(
                self.user_cloud.compute.share_attachments(self.server)
            )
            self.assertEqual(1, len(server_shares))
            self.assertIsInstance(
                server_shares[0],
                server_share_.ShareMapping,
            )

            if server_shares[0].status == 'active':
                break

        LOG.debug(server_share)
        self.assertEqual(server_shares[0].status, 'active')
        self.assertEqual(server_shares[0].tag, 'mytag')

        # Stop server
        self.user_cloud.compute.stop_server(self.server.id)
        self.user_cloud.compute.wait_for_server(
            self.server,
            status='SHUTOFF',
            wait=self._wait_for_timeout,
        )

        # Delete the server share
        result = self.user_cloud.compute.delete_share_attachment(
            self.server,
            self.share.id,
        )
        self.assertIsNone(result)

        for count in utils.iterate_timeout(
            self._wait_for_timeout, message="Wait proper deletion of the share"
        ):
            server_shares = list(
                self.user_cloud.compute.share_attachments(self.server)
            )
            if len(server_shares) == 0:
                break

        self.assertEqual(0, len(server_shares))
