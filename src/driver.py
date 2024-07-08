from __future__ import annotations

from cloudshell.shell.core.driver_context import (
    AutoLoadCommandContext,
    AutoLoadDetails,
    InitCommandContext,
    ResourceCommandContext,
)
from cloudshell.shell.core.driver_utils import GlobalLock
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
from cloudshell.shell.standards.pdu.autoload_model import PDUResourceModel
from cloudshell.shell.standards.pdu.driver_interface import PDUResourceDriverInterface
from cloudshell.shell.standards.pdu.resource_config import RESTAPIPDUResourceConfig

from cloudshell.server_tech.flows.server_tech_autoload_flow import (
    ServerTechAutoloadFlow
)
from cloudshell.server_tech.flows.server_tech_state_flow import (
    ServerTechOutletsStateFlow
)


class ServerTechnologyShellDriver(ResourceDriverInterface, PDUResourceDriverInterface):
    SUPPORTED_OS = ["Server Technology PDU"]
    SHELL_NAME = "Server Technology PDU 2G"

    def __init__(self):
        self._cli = None

    def initialize(self, context: InitCommandContext) -> str:
        # api = CloudShellSessionContext(context).get_api()
        # resource_config = RESTAPIPDUResourceConfig.from_context(context, api)
        return "Finished initializing"

    @GlobalLock.lock
    def get_inventory(self, context: AutoLoadCommandContext) -> AutoLoadDetails:
        """Return device structure with all standard attributes.

        resource = Raritan.create_from_context(context)
        resource.vendor = 'specify the shell vendor'
        resource.model = 'specify the shell model'

        p1 = PowerSocket('p1')
        resource.add_sub_resource('1', p1)
        return resource.create_autoload_details()
        """

        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()
            resource_config = RESTAPIPDUResourceConfig.from_context(context, api)

            resource_model = PDUResourceModel.from_resource_config(resource_config)
            autoload_operations = ServerTechAutoloadFlow(config=resource_config)
            logger.info("Autoload started")
            response = autoload_operations.discover(self.SUPPORTED_OS, resource_model)
            logger.info("Autoload completed")
            return response

    def _change_power_state(
            self,
            context: ResourceCommandContext,
            ports: list[str],
            state: str
    ) -> None:  # noqa E501
        """Set power outlets state based on provided data."""
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = RESTAPIPDUResourceConfig.from_context(context, api)

            outlets_operations = ServerTechOutletsStateFlow(config=resource_config)
            logger.info(f"Power {state.capitalize()} operation started")
            outlets_operations.set_outlets_state(
                ports=ports,
                state=state,
            )
            logger.info(f"Power {state.capitalize()} operation completed")

    def PowerOn(self, context: ResourceCommandContext, ports: list[str]) -> None:
        """Set power state as ON to provided outlets."""
        self._change_power_state(context=context, ports=ports, state="on")

    def PowerOff(self, context: ResourceCommandContext, ports: list[str]) -> None:
        """Set power state as OFF to provided outlets."""
        self._change_power_state(context=context, ports=ports, state="off")

    def PowerCycle(
        self,
        context: ResourceCommandContext,
        ports: list[str],
        delay: str
    ) -> None:  # noqa E501
        """Set power state as CYCLE to provided outlets."""
        self._change_power_state(context=context, ports=ports, state="reboot")

    def cleanup(self):
        """Destroy the driver session.

        This function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass
