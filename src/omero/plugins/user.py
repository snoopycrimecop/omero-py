#!/usr/bin/env python
"""
   User administration plugin

   Copyright 2009 Glencoe Software, Inc. All rights reserved.
   Use is subject to license terms supplied in LICENSE.txt

"""

import os
import sys

from omero.cli import BaseControl, CLI

HELP = "Support for adding and managing users"

class UserControl(BaseControl):

    def _configure(self, parser):
        sub = parser.sub()

        add = parser.add(sub, self.add, help = "Add users")
        add.add_argument("-m", "--middlename", help = "Middle name, if available")
        add.add_argument("-e", "--email")
        add.add_argument("-i", "--institution")
        # Capitalized since conflict with main values
        add.add_argument("-P", "--userpassword", help = "Password for user")
        add.add_argument("-a", "--admin", help = "Whether the user should be an admin")
        add.add_argument("username", help = "User's login name")
        add.add_argument("firstname", help = "User's given name")
        add.add_argument("lastname", help = "User's surname name")
        add.add_argument("group", nargs="+", help = "Groups which the user is a member of")

        list = parser.add(sub, self.list, help = "List current users")

        password = parser.add(sub, self.password, help = "Set user's password")
        password.add_argument("username", nargs="?", help = "Username if not the current user")

    def password(self, args):
        from omero.rtypes import rstring
        client = self.ctx.conn(args)
        admin = client.sf.getAdminService()
        pw = self._ask_for_password(" to be set")
        pw = rstring(pw)
        if args.username:
            admin.changeUserPassword(args.username, pw)
        else:
            admin.changePassword(pw)
        self.ctx.out("Password changed")

    def list(self, args):
        c = self.ctx.conn(args)
        users = c.sf.getAdminService().lookupExperimenters()
        users = sorted([x.omeName.val for x in users])
        for u in users:
            self.ctx.out(u)

    def add(self, args):
        email = args.email
        login = args.username
        first = args.firstname
        middle = args.middlename
        last = args.lastname
        inst = args.institution
        pasw = args.userpassword

        from omero.rtypes import rstring
	from omero_model_ExperimenterI import ExperimenterI as Exp
	from omero_model_ExperimenterGroupI import ExperimenterGroupI as Grp
        c = self.ctx.conn(args)
	p = c.ic.getProperties()
	e = Exp()
	e.omeName = rstring(login)
	e.firstName = rstring(first)
	e.lastName = rstring(last)
	e.middleName = rstring(middle)
	e.email = rstring(email)
	e.institution = rstring(inst)
	admin = c.getSession().getAdminService()

        groups = [admin.lookupGroup(group) for group in args.group]
        roles = admin.getSecurityRoles()
        groups.append(Grp(roles.userGroupId, False))
        if args.admin:
            groups.append(Grp(roles.systemGroupId, False))

        group = groups.pop(0)

        if pasw is None:
            id = admin.createExperimenter(e, group, groups)
            self.ctx.out("Added user %s" % id)
        else:
            id = admin.createExperimenterWithPassword(e, rstring(pasw), group, groups)
            self.ctx.out("Added user %s with password" % id)

try:
    register("user", UserControl, HELP)
except NameError:
    if __name__ == "__main__":
        cli = CLI()
        cli.register("user", UserControl, HELP)
        cli.invoke(sys.argv[1:])

