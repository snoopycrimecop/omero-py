#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2014 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from test.integration.clitest.cli import CLITest
from omero.cli import NonZeroReturnCode
import pytest

permissions = ["rw----", "rwr---", "rwra--", "rwrw--"]


class TestSessions(CLITest):

    def setup_method(self, method):
        super(TestSessions, self).setup_method(method)
        self.args += ["sessions"]

    def set_login_args(self, user):
        host = self.root.getProperty("omero.host")
        port = self.root.getProperty("omero.port")
        self.args = ["sessions", "login"]
        self.conn_string = "%s@%s:%s" % (user.omeName.val, host, port)
        self.args += [self.conn_string]

    def get_connection_string(self):
        ec = self.cli.get_event_context()
        return 'session %s (%s). Idle timeout: 10.0 min. ' \
            'Current group: %s\n' % (ec.sessionUuid, self.conn_string,
                                     ec.groupName)

    def check_sudoer(self, target_user, sudoer, group=None):
        self.set_login_args(target_user)
        self.args += ["--sudo", sudoer.omeName.val]
        self.args += ["-w", sudoer.omeName.val]
        if group:
            self.args += ["-g", group.name.val]
        self.cli.invoke(self.args, strict=True)
        ec = self.cli.controls["sessions"].ctx._event_context
        assert ec.userName == target_user.omeName.val
        if group:
            assert ec.groupName == group.name.val
        self.cli.invoke(["sessions", "logout"], strict=True)

    # Login subcommand
    # ========================================================================
    @pytest.mark.parametrize("quiet", [True, False])
    def testLoginStderr(self, capsys, quiet):
        user = self.new_user()
        self.set_login_args(user)
        self.args += ["-w", user.omeName.val]
        if quiet:
            self.args += ["-q"]
        self.cli.invoke(self.args, strict=True)
        o, e = capsys.readouterr()
        assert not o
        if quiet:
            assert not e
        else:
            assert e == 'Created ' + self.get_connection_string()

        join_args = ["sessions", "login", self.conn_string]
        if quiet:
            join_args += ["-q"]
        self.cli.invoke(join_args, strict=True)
        o, e = capsys.readouterr()
        assert not o
        if quiet:
            assert not e
        else:
            assert e == 'Using ' + self.get_connection_string()

        host = self.root.getProperty("omero.host")
        port = self.root.getProperty("omero.port")
        ec = self.cli.get_event_context()
        join_args = ["sessions", "login", "-k", ec.sessionUuid,
                     "%s:%s" % (host, port)]
        if quiet:
            join_args += ["-q"]
        self.cli.invoke(join_args, strict=True)
        o, e = capsys.readouterr()
        assert not o
        if quiet:
            assert not e
        else:
            assert e == 'Joined ' + self.get_connection_string()

    @pytest.mark.parametrize("perms", permissions)
    def testLoginAs(self, perms):
        """Test the login --sudo functionality"""

        group1 = self.new_group(perms=perms)
        group2 = self.new_group(perms=perms)
        admin = self.root.sf.getAdminService()
        user = self.new_user(group1, owner=False)  # Member of two groups
        admin.addGroups(user, [group2])
        member = self.new_user(group1, owner=False)  # Member of first gourp
        owner = self.new_user(group1, owner=True)  # Owner of first group
        admin = self.new_user(system=True)  # System administrator

        # Administrator are in the list of sudoers
        self.check_sudoer(user, admin)
        self.check_sudoer(user, admin, group1)
        self.check_sudoer(user, admin, group2)

        # Group owner is in the list of sudoers
        self.check_sudoer(user, owner)
        self.check_sudoer(user, admin, group1)
        self.check_sudoer(user, admin, group2)

        # Other group members are not sudoers
        with pytest.raises(NonZeroReturnCode):
            self.check_sudoer(user, member)

    @pytest.mark.parametrize('with_sudo', [True, False])
    @pytest.mark.parametrize('with_group', [True, False])
    def testLoginMultiGroup(self, with_sudo, with_group):
        group1 = self.new_group()
        client, user = self.new_client_and_user(group=group1)
        group2 = self.new_group([user])

        self.set_login_args(user)
        if with_sudo:
            self.args += ["--sudo", "root"]
            self.args += ["-w", self.root.getProperty("omero.rootpass")]
        else:
            self.args += ["-w", user.omeName.val]
        if with_group:
            self.args += ["-g", group2.name.val]
        self.cli.invoke(self.args, strict=True)
        ec = self.cli.get_event_context()
        assert ec.userName == user.omeName.val
        if with_group:
            assert ec.groupName == group2.name.val
        else:
            assert ec.groupName == group1.name.val

    # Group subcommand
    # ========================================================================
    def testGroup(self):
        group1 = self.new_group()
        client, user = self.new_client_and_user(group=group1)
        group2 = self.new_group([user])

        self.set_login_args(user)
        self.args += ["-w", user.omeName.val]
        self.cli.invoke(self.args, strict=True)
        ec = self.cli.get_event_context()
        assert ec.groupName == group1.name.val

        self.args = ["sessions", "group", group2.name.val]
        self.cli.invoke(self.args, strict=True)
        ec = self.cli.get_event_context()
        assert ec.groupName == group2.name.val
