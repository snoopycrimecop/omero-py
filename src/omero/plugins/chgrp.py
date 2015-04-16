#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2011 Glencoe Software, Inc. All Rights Reserved.
# Use is subject to license terms supplied in LICENSE.txt
#

"""
   chgrp plugin

   Plugin read by omero.cli.Cli during initialization. The method(s)
   defined here will be added to the Cli class for later use.
"""

from omero.cli import CLI, GraphControl, ExperimenterGroupArg
import sys

HELP = """Move data between groups

Example Usage:

  omero chgrp 101 Image:1                     # Move all of Image 1 to \
group 101
  omero chgrp Group:101 Image:1               # Move all of Image 1 to \
group 101
  omero chgrp ExperimenterGroup:101 Image:1   # Move all of Image 1 to \
group 101
  omero chgrp "My Lab" Image:1,2,3            # Move all of Images 1, 2 and 3 \
to group "myLab"

  omero chgrp --exclude Image Plate:1         # Calls chgrp on Plate, \
leaving all
                                              # images in the previous group.

  What data is moved is the same as that which would be deleted by a similar
  call to "omero delete Image:1"

"""


class ChgrpControl(GraphControl):

    def cmd_type(self):
        import omero
        import omero.all
        return omero.cmd.Chgrp2

    def _pre_objects(self, parser):
        parser.add_argument(
            "grp", nargs="?", type=ExperimenterGroupArg,
            help="""Group to move objects to""")

    def _process_request(self, req, args, client):
        # Retrieve group id
        gid = args.grp.lookup(client)
        if gid is None:
            self.ctx.die(196, "Failed to find group: %s" % args.grp.orig)

        # Retrieve group
        import omero
        try:
            group = client.sf.getAdminService().getGroup(gid)
        except omero.ApiUsageException:
            self.ctx.die(196, "Failed to find group: %s" % args.grp.orig)

        # Check session owner is member of the target group
        uid = client.sf.getAdminService().getEventContext().userId
        ids = [x.child.id.val for x in group.copyGroupExperimenterMap()]
        if uid not in ids:
            self.ctx.die(197, "Current user is not member of group: %s" %
                         group.id.val)

        # Set requests group
        for request in req.requests:
            request.groupId = gid

        super(ChgrpControl, self)._process_request(req, args, client)

try:
    register("chgrp", ChgrpControl, HELP)
except NameError:
    if __name__ == "__main__":
        cli = CLI()
        cli.register("chgrp", ChgrpControl, HELP)
        cli.invoke(sys.argv[1:])
