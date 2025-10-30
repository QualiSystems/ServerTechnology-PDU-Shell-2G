from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from attrs import define
from cloudshell.shell.standards.pdu.resource_config import RESTAPIPDUResourceConfig

from server_tech.handlers.rest_api_handler import ServerTechAPI

if TYPE_CHECKING:
    from typing_extensions import Self

logger = logging.getLogger(__name__)


@define(slots=False)
class ServerTechHandler:
    _obj: ServerTechAPI

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    @classmethod
    def from_config(cls, conf: RESTAPIPDUResourceConfig) -> ServerTechHandler:
        logger.info("Initializing Server Technology API client.")
        api = ServerTechAPI(
            address=conf.address,
            username=conf.api_user,
            password=conf.api_password,
            port=conf.api_port or None,
            scheme=conf.api_scheme or None,
        )
        return cls(api)

    def get_pdu_info(self):
        """Get basic information about PDU."""
        pdu_info = {}

        units_info = self._obj.get_pdu_units_info()
        for unit in units_info:
            pdu_info.update(
                {
                    "model": unit.get("model_number", ""),
                    "serial": unit.get("product_serial_number", ""),
                }
            )

        system_data = self._obj.get_pdu_system_info()
        pdu_info.update({"fw": system_data.get("firmware", "")})

        return pdu_info

    def get_outlets_info(self):
        """Get information about outlets."""
        outlets_info = {}

        outlets = self._obj.get_outlets()
        for outlet in outlets:
            outlets_info.update({outlet["id"]: outlet["control_state"]})

        return outlets_info

    def set_outlet_state(self, outlet_id: str, outlet_state: str):
        """Set outlet state."""
        self._obj.set_outlet_state(outlet_id=outlet_id, outlet_state=outlet_state)
