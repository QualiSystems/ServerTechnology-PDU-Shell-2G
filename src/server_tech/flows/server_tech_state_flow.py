from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define

from server_tech.helpers.errors import NotSupportedServerTechError

if TYPE_CHECKING:
    from server_tech.handlers.server_tech_handler import ServerTechHandler


@define
class ServerTechOutletsStateFlow:
    _si: ServerTechHandler

    AVAILABLE_STATES = ["on", "off", "reboot"]

    @staticmethod
    def _ports_to_outlet_ids(ports: list[str]) -> list[str]:
        """Convert ports to the suitable format."""
        return [port.split("/")[-1].replace("PS", "") for port in ports]

    def set_outlets_state(self, ports: list[str], state: str) -> None:
        """Set Outlet/Outlets state.

        Change outlet or list of outlets state to the provided state.
        :param ports: ['192.168.30.128/PS4', '192.168.30.128/PS6']
        :param state: outlet state to be set. Possible values: on, off, reboot
        """
        if state not in self.AVAILABLE_STATES:
            raise NotSupportedServerTechError(f"State '{state}' is not supported.")

        outlets = ServerTechOutletsStateFlow._ports_to_outlet_ids(ports=ports)

        for outlet_id in outlets:
            self._si.set_outlet_state(outlet_id=outlet_id, outlet_state=state)
