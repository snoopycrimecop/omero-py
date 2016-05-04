#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2009-2014 Glencoe Software, Inc. All Rights Reserved.
# Use is subject to license terms supplied in LICENSE.txt
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

"""
   Startup plugin for command-line importer.

"""

import os
import csv
import sys
import shlex
import fileinput

from omero.cli import BaseControl, CLI
import omero.java
from omero_ext.argparse import SUPPRESS
from path import path

START_CLASS = "ome.formats.importer.cli.CommandLineImporter"
TEST_CLASS = "ome.formats.test.util.TestEngine"

HELP = """Run the Java-based command-line importer

This is a Python wrapper around the Java importer. Login is handled by Python
OMERO.cli. To see more options, use "--javahelp".

Options marked with "**" are passed strictly to Java. If they interfere with
any of the Python arguments, you may need to end precede your arguments with a
"--".
"""
EXAMPLES = """
Examples:

  # Display help
  $ bin/omero import -h
  # Import foo.tiff using current login
  $ bin/omero import ~/Data/my_file.dv
  # Import foo.tiff using input credentials
  $ bin/omero import -s localhost -u user -w password foo.tiff
  # Set Java debugging level to ALL
  $ bin/omero import foo.tiff -- --debug=ALL
  # Display used files for importing foo.tiff
  $ bin/omero import foo.tiff -f
  # Limit debugging output
  $ bin/omero import -- --debug=ERROR foo.tiff

For additional information, see:
http://www.openmicroscopy.org/site/support/omero5.2/users/cli/import.html
Report bugs to <ome-users@lists.openmicroscopy.org.uk>
"""
TESTHELP = """Run the Importer TestEngine suite (devs-only)"""
DEBUG_CHOICES = ["ALL", "DEBUG", "ERROR", "FATAL", "INFO", "TRACE", "WARN"]
OUTPUT_CHOICES = ["legacy", "yaml"]
SKIP_CHOICES = ['all', 'checksum', 'minmax', 'thumbnails', 'upgrade']


class CommandArguments(object):

    def __init__(self, ctx, args):
        self.__args = args
        self.command_args = []
        self.set_login_arguments(ctx, args)
        self.set_skip_arguments(args)
        # Python arguments
        skip_list = (
            "javahelp", "skip", "file", "errs", "logback",
            "port", "password", "group", "create", "func",
            "bulk", "prog", "user", "key", "path", "logprefix",
            "JAVA_DEBUG", "quiet", "server", "depth", "clientdir")

        for key in vars(args):

            val = getattr(args, key)
            if key in skip_list:
                setattr(self, key, val)

            elif not val:
                pass

            elif len(key) == 1:
                self.command_args.append("-"+key)
                if isinstance(val, (str, unicode)):
                    self.command_args.append(val)
            else:
                self.command_args.append(
                    "--%s=%s" % (key, val))

    def __iter__(self):
        return iter([] + self.command_args + self.__args.path)

    def set_login_arguments(self, ctx, args):
        """Set the connection arguments"""

        if args.javahelp:
            self.command_args.append("-h")

        # Connection is required unless help arguments or -f is passed
        connection_required = ("-h" not in self.command_args and
                               not args.f and
                               not args.advanced_help)
        if connection_required:
            client = ctx.conn(args)
            self.command_args.extend(["-s", client.getProperty("omero.host")])
            self.command_args.extend(["-p", client.getProperty("omero.port")])
            self.command_args.extend(["-k", client.getSessionId()])

    def set_skip_arguments(self, args):
        """Set the arguments to skip steps during import"""
        if not args.skip:
            return

        if ('all' in args.skip or 'checksum' in args.skip):
            self.command_args.append("--checksum-algorithm=File-Size-64")
        if ('all' in args.skip or 'thumbnails' in args.skip):
            self.command_args.append("--no-thumbnails")
        if ('all' in args.skip or 'minmax' in args.skip):
            self.command_args.append("--no-stats-info")
        if ('all' in args.skip or 'upgrade' in args.skip):
            self.command_args.append("--no-upgrade-check")

    def open_files(self):
        # Open file handles for stdout/stderr if applicable
        out = self.open_log(self.__args.file, self.__args.logprefix)
        err = self.open_log(self.__args.errs, self.__args.logprefix)
        return out, err

    def open_log(self, file, prefix=None):
        if not file:
            return None
        if prefix:
            file = os.path.sep.join([prefix, file])
        dir = os.path.dirname(file)
        if not os.path.exists(dir):
            os.makedirs(dir)
        return open(file, "w")


class ImportControl(BaseControl):

    COMMAND = [START_CLASS]

    def _configure(self, parser):

        parser.add_login_arguments()

        def add_python_argument(*args, **kwargs):
            parser.add_argument(*args, **kwargs)

        add_python_argument(
            "--javahelp", "--java-help",
            action="store_true", help="Show the Java help text")

        parser.add_argument(  # Special?
            "--advanced-help", action="store_true",
            help="Show the advanced help text")

        add_python_argument(
            "---bulk", nargs="?",
            help="Bulk YAML file for driving multiple imports")
        add_python_argument(
            "---logprefix", nargs="?",
            help="Directory or file prefix to prepend to ---file and ---errs")
        add_python_argument(
            "---file", nargs="?",
            help="File for storing the standard out of the Java process")
        add_python_argument(
            "---errs", nargs="?",
            help="File for storing the standard err of the Java process")

        add_python_argument(
            "--clientdir", type=str,
            help="Path to the directory containing the client JARs. "
            " Default: lib/client")
        add_python_argument(
            "--logback", type=str,
            help="Path to a logback xml file. "
            " Default: etc/logback-cli.xml")

        # The following arguments are strictly passed to Java
        name_group = parser.add_argument_group(
            'Naming arguments', 'Optional arguments passed strictly to Java.')

        def add_java_name_argument(*args, **kwargs):
            name_group.add_argument(*args, **kwargs)

        add_java_name_argument(
            "-n", "--name",
            help="Image or plate name to use (**)",
            metavar="NAME")
        add_java_name_argument(
            "-x", "--description",
            help="Image or plate description to use (**)",
            metavar="DESCRIPTION")
        # Deprecated naming arguments
        add_java_name_argument(
            "--plate_name",
            help=SUPPRESS)
        add_java_name_argument(
            "--plate_description",
            help=SUPPRESS)

        # Feedback options
        feedback_group = parser.add_argument_group(
            'Feedback arguments',
            'Optional arguments passed strictly to Java allowing to report'
            ' errors to the OME team.')

        def add_feedback_argument(*args, **kwargs):
            feedback_group.add_argument(*args, **kwargs)

        add_feedback_argument(
            "--report", action="store_true",
            help="Report errors to the OME team (**)")
        add_feedback_argument(
            "--upload", action="store_true",
            help=("Upload broken files and log file (if any) with report."
                  " Required --report (**)"))
        add_feedback_argument(
            "--logs", action="store_true",
            help=("Upload log file (if any) with report."
                  " Required --report (**)"))
        add_feedback_argument(
            "--email",
            help="Email for reported errors. Required --report (**)",
            metavar="EMAIL")
        add_feedback_argument(
            "--qa-baseurl",
            help=SUPPRESS)

        # Annotation options
        annotation_group = parser.add_argument_group(
            'Annotation arguments',
            'Optional arguments passed strictly to Java allowing to annotate'
            ' imports.')

        def add_annotation_argument(*args, **kwargs):
            annotation_group.add_argument(*args, **kwargs)

        add_annotation_argument(
            "--annotation-ns", metavar="ANNOTATION_NS",
            help="Namespace to use for subsequent annotation (**)")
        add_annotation_argument(
            "--annotation-text", metavar="ANNOTATION_TEXT",
            help="Content for a text annotation (requires namespace) (**)")
        add_annotation_argument(
            "--annotation-link",
            metavar="ANNOTATION_LINK",
            help="Comment annotation ID to link all images to (**)")
        add_annotation_argument(
            "--annotation_ns", metavar="ANNOTATION_NS",
            help=SUPPRESS)
        add_annotation_argument(
            "--annotation_text", metavar="ANNOTATION_TEXT",
            help=SUPPRESS)
        add_annotation_argument(
            "--annotation_link", metavar="ANNOTATION_LINK",
            help=SUPPRESS)

        java_group = parser.add_argument_group(
            'Java arguments', 'Optional arguments passed strictly to Java')

        def add_java_argument(*args, **kwargs):
            java_group.add_argument(*args, **kwargs)

        add_java_argument(
            "-f", action="store_true",
            help="Display the used files and exit (**)")
        add_java_argument(
            "-c", action="store_true",
            help="Continue importing after errors (**)")
        add_java_argument(
            "-l",
            help="Use the list of readers rather than the default (**)",
            metavar="READER_FILE")
        add_java_argument(
            "-d",
            help="OMERO dataset ID to import image into (**)",
            metavar="DATASET_ID")
        add_java_argument(
            "-r",
            help="OMERO screen ID to import plate into (**)",
            metavar="SCREEN_ID")
        add_java_argument(
            "-T", "--target",
            help="OMERO target specification (**)",
            metavar="TARGET")
        add_java_argument(
            "--debug", choices=DEBUG_CHOICES,
            help="Turn debug logging on (**)",
            metavar="LEVEL", dest="JAVA_DEBUG")
        add_java_argument(
            "--output", choices=OUTPUT_CHOICES,
            help="Set an alternative output style",
            metavar="TYPE")

        # Unsure on these.
        add_python_argument(
            "--depth", default=4, type=int,
            help="Number of directories to scan down for files")
        add_python_argument(
            "--skip", type=str, choices=SKIP_CHOICES, action='append',
            help="Optional step to skip during import")
        add_python_argument(
            "path", nargs="*",
            help="Path to be passed to the Java process")

        parser.set_defaults(func=self.importer)

    def importer(self, args):

        if args.clientdir:
            client_dir = path(args.clientdir)
        else:
            client_dir = self.ctx.dir / "lib" / "client"
        etc_dir = self.ctx.dir / "etc"
        if args.logback:
            xml_file = path(args.logback)
        else:
            xml_file = etc_dir / "logback-cli.xml"
        logback = "-Dlogback.configurationFile=%s" % xml_file

        try:
            classpath = [file.abspath() for file in client_dir.files("*.jar")]
        except OSError as e:
            self.ctx.die(102, "Cannot get JAR files from '%s' (%s)"
                         % (client_dir, e.strerror))
        if not classpath:
            self.ctx.die(103, "No JAR files found under '%s'" % client_dir)

        command_args = CommandArguments(self.ctx, args)
        xargs = [logback, "-Xmx1024M", "-cp", os.pathsep.join(classpath)]
        xargs.append("-Domero.import.depth=%s" % args.depth)

        if args.bulk and args.path:
            self.ctx.die(104, "When using bulk import, omit paths")
        elif args.bulk:
            self.bulk_import(command_args, xargs)
        else:
            self.do_import(command_args, xargs)

    def do_import(self, command_args, xargs):
        out = err = None
        try:
            import_command = self.COMMAND + list(command_args)
            if self.ctx.isdebug:
                self.ctx.err("COMMAND:%s" % " ".join(import_command))
            out, err = command_args.open_files()

            p = omero.java.popen(
                import_command, debug=False, xargs=xargs,
                stdout=out, stderr=err)

            self.ctx.rv = p.wait()

        finally:
            # Make sure file handles are closed
            if out:
                out.close()
            if err:
                err.close()

    def bulk_import(self, command_args, xargs):

        try:
            from yaml import safe_load
        except ImportError:
            self.ctx.die(105, "yaml is unsupported")

        old_pwd = os.getcwd()
        try:

            # Walk the .yml graph looking for includes
            # and load them all so that the top parent
            # values can be overwritten.
            contents = list()
            bulkfile = command_args.bulk
            while bulkfile:
                bulkfile = os.path.abspath(bulkfile)
                parent = os.path.dirname(bulkfile)
                with open(bulkfile, "r") as f:
                    data = safe_load(f)
                    contents.append((bulkfile, parent, data))
                    bulkfile = data.get("include")
                    os.chdir(parent)
                    # TODO: include file are updated based on the including file
                    # but other file paths aren't!

            bulk = dict()
            for bulkfile, parent, data in reversed(contents):
                bulk.update(data)
                os.chdir(parent)

            self.optionally_add(command_args, bulk, "name")
            # TODO: need better mapping
            self.optionally_add(command_args, bulk, "continue", "java_c")

            for step in self.parse_bulk(bulk, command_args):
                self.do_import(command_args, xargs)
                if self.ctx.rv:
                    if command_args.java_c:
                        msg = "Import failed with error code: %s. Continuing"
                        self.ctx.err(msg % self.ctx.rv)
                    else:
                        msg = "Import failed. Use -c to continue after errors"
                        self.ctx.die(106, msg)
        finally:
            os.chdir(old_pwd)

    def optionally_add(self, command_args, bulk, key, dest=None):
        if dest is None:
            dest = "java_" + key
        if key in bulk:
            setattr(command_args, dest, bulk[key])

    def parse_bulk(self, bulk, command_args):
        path = bulk["path"]
        cols = bulk.get("columns")

        if not cols:
            # No parsing necessary
            command_args.path = [path]

        else:
            function = self.parse_text
            if path.endswith(".tsv"):
                function = self.parse_tsv
            elif path.endswith(".csv"):
                function = self.parse_csv

            for parts in function(path):
                for idx, col in enumerate(cols):
                    if col == "path":
                        command_args.path = [parts[idx]]
                    elif hasattr(command_args, "java_%s" % col):
                        setattr(command_args, "java_%s" % col, parts[idx])
                    else:
                        setattr(command_args, col, parts[idx])
                yield parts

    def parse_text(self, path):
        for line in fileinput.input([path]):
            line = line.strip()
            yield shlex.split(line)

    def parse_tsv(self, path, delimiter="\t"):
        for line in self.parse_csv(path, delimiter):
            yield line

    def parse_csv(self, path, delimiter=","):
        with open(path, "r") as data:
            for line in csv.reader(data, delimiter=delimiter):
                yield line


class TestEngine(ImportControl):
    COMMAND = [TEST_CLASS]

try:
    register("import", ImportControl, HELP, epilog=EXAMPLES)
    register("testengine", TestEngine, TESTHELP)
except NameError:
    if __name__ == "__main__":
        cli = CLI()
        cli.register("import", ImportControl, HELP, epilog=EXAMPLES)
        cli.register("testengine", TestEngine, TESTHELP)
        cli.invoke(sys.argv[1:])
