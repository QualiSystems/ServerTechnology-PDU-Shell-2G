from __future__ import annotations

import logging
import ssl
from abc import abstractmethod
from collections.abc import Callable

from attrs import define, field
from attrs.setters import frozen

import requests
import urllib3


from cloudshell.server_tech.helpers.errors import (
    BaseServerTechError,
    RESTAPIServerTechError,
)

logger = logging.getLogger(__name__)


@define
class BaseAPIClient:
    address: str = field(on_setattr=frozen)
    username: str = field(on_setattr=frozen)
    password: str = field(on_setattr=frozen)
    session: requests.Session = field(on_setattr=frozen, default=requests.Session())
    scheme: str = field(on_setattr=frozen, default="https")
    port: int = field(on_setattr=frozen, default=443)
    verify_ssl: bool = field(on_setattr=frozen, default=ssl.CERT_NONE)

    def __attrs_post_init__(self):
        self.session.verify = self.verify_ssl
        if self.username:
            self.session.auth = (self.username, self.password)
        self.session.headers.update({"Content-Type": "application/json"})
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    @abstractmethod
    def _base_url(self):
        pass

    def _do_request(
        self,
        method: Callable,
        path: str,
        raise_for_status: bool = True,
        http_error_map: dict[int, Exception | type[Exception]] | None = None,
        **kwargs: dict,
    ) -> requests.Response:
        if http_error_map is None:
            http_error_map = {}

        url = f"{self._base_url()}/{path}"
        res = method(url=url, **kwargs)
        try:
            raise_for_status and res.raise_for_status()
        except requests.exceptions.HTTPError as caught_err:
            logger.exception(f"HTTP Error: {caught_err}")
            http_code = caught_err.response.status_code
            err = http_error_map.get(http_code, BaseServerTechError)
            raise err from caught_err
        return res

    def _do_get(
        self,
        path: str,
        raise_for_status: bool = True,
        http_error_map: dict[int, Exception | type[Exception]] | None = None,
        **kwargs: dict,
    ) -> requests.Response:
        """Basic GET request client method."""
        return self._do_request(
            self.session.get, path, raise_for_status, http_error_map, **kwargs
        )

    def _do_post(
        self,
        path: str,
        raise_for_status: bool = True,
        http_error_map: dict[int, Exception | type[Exception]] | None = None,
        **kwargs: dict,
    ) -> requests.Response:
        """Basic POST request client method."""
        return self._do_request(
            self.session.post, path, raise_for_status, http_error_map, **kwargs
        )

    def _do_put(
        self,
        path: str,
        raise_for_status: bool = True,
        http_error_map: dict[int, Exception] | None = None,
        **kwargs: dict,
    ) -> requests.Response:
        """Basic PUT request client method."""
        return self._do_request(
            self.session.put, path, raise_for_status, http_error_map, **kwargs
        )

    def _do_patch(
        self,
        path: str,
        raise_for_status: bool = True,
        http_error_map: dict[int, Exception | type[Exception]] | None = None,
        **kwargs: dict,
    ) -> requests.Response:
        """Basic PATCH request client method."""
        return self._do_request(
            self.session.patch, path, raise_for_status, http_error_map, **kwargs
        )

    def _do_delete(
        self,
        path: str,
        raise_for_status: bool = True,
        http_error_map: dict[int, Exception | type[Exception]] | None = None,
        **kwargs: dict,
    ) -> requests.Response:
        """Basic DELETE request client method."""
        return self._do_request(
            self.session.delete, path, raise_for_status, http_error_map, **kwargs
        )


@define
class ServerTechAPI(BaseAPIClient):
    BASE_ERRORS = {
        404: RESTAPIServerTechError,
        405: RESTAPIServerTechError,
        503: RESTAPIServerTechError,
    }
    """
    404 NOT FOUND Requested resource does not exist or is unavailable
    405 METHOD NOT ALLOWED Requested method was not permitted
    503 SERVICE UNAVAILABLE The server is too busy to send the resource or resource collection
    """

    def _base_url(self):
        # return f"{self.scheme}://{self.address}/jaws"
        return f"{self.scheme}://{self.address}:{self.port}/jaws"

    def get_pdu_info(self) -> dict[str, str]:
        """Get information about outlets."""
        pdu_info = {}
        error_map = {}

        units_data = self._do_get(
            path=f"config/info/units",
            http_error_map={**self.BASE_ERRORS, **error_map}
        ).json()

        for unit in units_data:
            pdu_info.update(
                {
                    "model": unit.get("model_number", ""),
                    "serial": unit.get("product_serial_number", ""),
                }
            )

        system_data = self._do_get(
            path=f"config/info/system",
            http_error_map={**self.BASE_ERRORS, **error_map}
        ).json()
        pdu_info.update({"fw": system_data.get("firmware", "")})
        return pdu_info

    def get_outlets(self) -> dict[str, str]:
        """Get information about outlets."""
        error_map = {}
        outlets_info = {}

        response = self._do_get(
            path=f"control/outlets",
            http_error_map={**self.BASE_ERRORS, **error_map}
        )
        for data in response.json():
            outlets_info.update({data["id"]: data["control_state"]})

        return outlets_info

    def set_outlet_state(self, outlet_id: str, outlet_state: str) -> None:
        """Set outlet state.

        Possible outlet states could be on/off/reboot.
        """
        error_map = {
            400: RESTAPIServerTechError,
            409: RESTAPIServerTechError
        }
        """
        400 BAD REQUEST Malformed patch document; a required patch object member is missing OR an unsupported operation was included.
        409 CONFLICT Property specified for updating does not exist in resource
        """
        self._do_patch(
            path=f"control/outlets/{outlet_id}",
            json={"control_action": outlet_state},
            http_error_map={**self.BASE_ERRORS, **error_map}
        )


"""
GET
200 OK Response contains JSON object with requested data
404 NOT FOUND Requested resource does not exist or is unavailable
405 METHOD NOT ALLOWED Requested method was not permitted
503 SERVICE UNAVAILABLE The server is too busy to send the resource or resource collection

PATCH
204 NO CONTENT Acknowledges that update was successful
400 BAD REQUEST Malformed patch document; a required patch object member is missing OR an unsupported operation was included.
404 NOT FOUND Requested resource does not exist or is unavailable
405 METHOD NOT ALLOWED Requested method was not permitted
409 CONFLICT Property specified for updating does not exist in resource
503 SERVICE UNAVAILABLE The server is too busy to update the resource

POST
201 CREATED Resource created successfully.
400 BAD REQUEST Message contained either bad values (e.g. out of range) for properties, or non-existent properties
404 NOT FOUND Requested resource collection does not exist or is unavailable
405 METHOD NOT ALLOWED Requested method was not permitted
409 CONFLICT Requested resource already exists
503 SERVICE UNAVAILABLE The server is too busy to create the resource

DELETE
204 NO CONTENT Resource was deleted successfully
400 BAD REQUEST Message contained data (must be empty)
403 FORBIDDEN Resource cannot be deleted
404 NOT FOUND Requested resource does not exist or is unavailable
405 METHOD NOT ALLOWED Requested method was not permitted
503 SERVICE UNAVAILABLE The server is too busy to delete the resource

"""
