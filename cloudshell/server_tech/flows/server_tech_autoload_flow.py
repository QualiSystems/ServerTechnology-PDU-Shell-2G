from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cloudshell.shell.flows.autoload.basic_flow import AbstractAutoloadFlow
from cloudshell.server_tech.handlers.rest_api_handler import ServerTechAPI

if TYPE_CHECKING:
    from cloudshell.shell.core.driver_context import AutoLoadDetails
    from cloudshell.shell.standards.pdu.resource_config import RESTAPIPDUResourceConfig
    from cloudshell.shell.standards.pdu.autoload_model import PDUResourceModel


logger = logging.getLogger(__name__)


class ServerTechAutoloadFlow(AbstractAutoloadFlow):
    """Autoload flow."""

    def __init__(self, config: RESTAPIPDUResourceConfig):
        super().__init__()
        self.config = config

    def _autoload_flow(
        self,
        supported_os: list[str],
        resource_model: PDUResourceModel
    ) -> AutoLoadDetails:
        """Autoload Flow."""
        logger.info("*" * 70)
        logger.info("Start discovery process .....")

        api = ServerTechAPI(
                address=self.config.address,
                username=self.config.api_user,
                password=self.config.api_password,
                port=self.config.api_port or None,
                scheme=self.config.api_scheme or None,
            )

        outlets_info = api.get_outlets()
        pdu_info = api.get_pdu_info()

        resource_model.vendor = "Server Technology"
        resource_model.model = pdu_info.get("model", "")

        for outlet_id, outlet_state in outlets_info.items():
            outlet_object = resource_model.entities.PowerSocket(index=outlet_id)
            resource_model.connect_power_socket(outlet_object)

        autoload_details = resource_model.build()
        logger.info("Discovery process finished successfully")

        return autoload_details
