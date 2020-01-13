# Summary hub classes
#
# Copyright (C) 2011  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Chris Lumens <clumens@redhat.com>
#
from pyanaconda.constants import WARNING_SMT_ENABLED_GUI
from pyanaconda.i18n import _, C_
from pyanaconda.iutil import is_smt_enabled
from pyanaconda.ui.gui.hubs import Hub
from pyanaconda.ui.gui.spokes.lib.detailederror import DetailedErrorDialog
from pyanaconda.ui.lib.space import FileSystemSpaceChecker, DirInstallSpaceChecker
from pyanaconda.flags import flags

__all__ = ["SummaryHub"]

class SummaryHub(Hub):
    builderObjects = ["summaryWindow"]
    mainWidgetName = "summaryWindow"
    uiFile = "hubs/summary.glade"
    helpFile = "SummaryHub.xml"

    def __init__(self, data, storage, payload, instclass):
        """Create a new Hub instance.

           The arguments this base class accepts defines the API that Hubs
           have to work with.  A Hub does not get free reign over everything
           in the anaconda class, as that would be a big mess.  Instead, a
           Hub may count on the following:

           ksdata       -- An instance of a pykickstart Handler object.  The
                           Hub uses this to populate its UI with defaults
                           and to pass results back after it has run.
           storage      -- An instance of storage.Storage.  This is useful for
                           determining what storage devices are present and how
                           they are configured.
           payload      -- An instance of a packaging.Payload subclass.  This
                           is useful for displaying and selecting packages to
                           install, and in carrying out the actual installation.
           instclass    -- An instance of a BaseInstallClass subclass.  This
                           is useful for determining distribution-specific
                           installation information like default package
                           selections and default partitioning.
        """
        super(SummaryHub, self).__init__(data, storage, payload, instclass)
        self._show_details_callback = None

        if not flags.dirInstall:
            self._checker = FileSystemSpaceChecker(storage, payload)
        else:
            self._checker = DirInstallSpaceChecker(storage, payload)

        # Add an info-bar-clicked handler
        self.window.connect("info-bar-clicked", self._on_info_bar_clicked)

    def _on_info_bar_clicked(self, *args):
        """Call the callback to show a detailed message."""
        if self._show_details_callback:
            self._show_details_callback()

    def _get_warning(self):
        """Get the warning message for the hub."""
        warning = super(SummaryHub, self)._get_warning()
        callback = None

        if not warning and is_smt_enabled():
            warning = _("Warning: Processor has Simultaneous Multithreading (SMT) enabled.  "
                        "<a href=\"\">Click for details.</a>")

            callback = self._show_detailed_smt_warning

        self._show_details_callback = callback
        return warning

    def _show_detailed_smt_warning(self):
        """Show details for the SMT warning."""
        label = _("The following warnings were encountered when checking your kernel "
                  "configuration. These are not fatal, but you may wish to make changes "
                  "to your kernel config.")

        warning = _(WARNING_SMT_ENABLED_GUI)

        dialog = DetailedErrorDialog(
            self.data,
            buttons=[C_("GUI|Summary|Warning Dialog", "_OK")],
            label=label
        )

        with self.main_window.enlightbox(dialog.window):
            dialog.refresh(warning)
            dialog.run()

        dialog.window.destroy()
