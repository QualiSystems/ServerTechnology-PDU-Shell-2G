from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cloudshell.shell.flows.autoload.basic_flow import AbstractAutoloadFlow

if TYPE_CHECKING:
    from cloudshell.shell.core.driver_context import AutoLoadDetails
    from cloudshell.shell.standards.pdu.autoload_model import PDUResourceModel

    from server_tech.handlers.server_tech_handler import ServerTechHandler


logger = logging.getLogger(__name__)


class ServerTechAutoloadFlow(AbstractAutoloadFlow):
    """Autoload flow."""

    def __init__(self, si: ServerTechHandler):
        super().__init__()
        self._si = si

    def _autoload_flow(
        self, supported_os: list[str], resource_model: PDUResourceModel
    ) -> AutoLoadDetails:
        """Autoload Flow."""
        logger.info("*" * 70)
        logger.info("Start discovery process .....")

        outlets_info = self._si.get_outlets_info()
        pdu_info = self._si.get_pdu_info()

        resource_model.vendor = "Server Technology"
        resource_model.model = pdu_info.get("model", "")

        for outlet_id, outlet_state in outlets_info.items():
            outlet_object = resource_model.entities.PowerSocket(index=outlet_id)
            resource_model.connect_power_socket(outlet_object)

        autoload_details = resource_model.build()
        logger.info("Discovery process finished successfully")

        return autoload_details
