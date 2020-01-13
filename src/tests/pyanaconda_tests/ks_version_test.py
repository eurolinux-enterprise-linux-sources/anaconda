#!/usr/bin/python
#
# Copyright (C) 2013  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Chris Lumens <clumens@redhat.com>
import unittest
import os
from pyanaconda import kickstart


# Verify that each kickstart command in anaconda uses the correct version of
# that command as provided by pykickstart.  That is, if there's an FC3 and an
# F10 version of a command, make sure anaconda >= F10 uses the F10 version.
class CommandVersionTestCase(unittest.TestCase):

    def assert_compare_versions(self, children, parents):
        """Check if children inherit from parents."""
        for name in children:
            print(name, children[name], parents[name])
            self.assertIsInstance(children[name](), parents[name])

    def commands_test(self):
        """Test that anaconda uses the right versions of kickstart commands"""
        anaconda_cmds = kickstart.commandMap
        pykickstart_cmds = kickstart.superclass.commandMap
        self.assert_compare_versions(anaconda_cmds, pykickstart_cmds)

    def data_test(self):
        """Test that anaconda uses the right versions of kickstart data"""
        anaconda_data = kickstart.dataMap
        pykickstart_data = kickstart.superclass.dataMap
        self.assert_compare_versions(anaconda_data, pykickstart_data)

    def dracut_commands_test(self):
        """Test that dracut uses the right versions of kickstart commands"""
        # top_srcdir should have been set by nosetests.sh. If it wasn't, the KeyError
        # will fail the test.
        parse_kickstart_path = os.path.join(os.environ['top_srcdir'], 'dracut', 'parse-kickstart')

        import tempfile
        with tempfile.NamedTemporaryFile() as parse_temp:
            # Compile the file manually to a tempfile so that the import doesn't automatically
            # crud up the source directory with parse-kickstartc
            import py_compile
            parse_temp = tempfile.NamedTemporaryFile()
            py_compile.compile(parse_kickstart_path, parse_temp.name)

            # Use imp to pretend that hyphens are ok for module names
            import imp
            parse_module = imp.load_module('parse_kickstart', parse_temp.file,
                    parse_temp.name, ('', 'r', imp.PY_COMPILED))

        dracut_commands = parse_module.dracutCmds
        pykickstart_commands = kickstart.superclass.commandMap
        self.assert_compare_versions(dracut_commands, pykickstart_commands)
