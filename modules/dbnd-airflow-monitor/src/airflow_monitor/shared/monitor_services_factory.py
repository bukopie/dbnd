# © Copyright Databand.ai, an IBM Company 2022
from abc import ABC
from typing import ClassVar, Optional

import airflow_monitor

from airflow_monitor.shared.adapter.adapter import ThirdPartyInfo
from airflow_monitor.shared.base_server_monitor_config import BaseServerConfig
from airflow_monitor.shared.decorators import decorate_configuration_service
from airflow_monitor.shared.integration_management_service import (
    IntegrationManagementService,
)
from airflow_monitor.shared.reporting_service import ReportingService


class MonitorServicesFactory(ABC):
    """
    This class is a factory that returns all the required components for running a monitor
    Inherit from this class, implement the methods and pass it to a MultiServerMonitor instance.
    """

    MONITOR_TYPE: ClassVar[str]

    def get_integration_management_service(self) -> IntegrationManagementService:
        return decorate_configuration_service(
            IntegrationManagementService(
                monitor_type=self.MONITOR_TYPE, server_monitor_config=BaseServerConfig
            )
        )

    @property
    def reporting_service(self) -> ReportingService:
        return ReportingService(monitor_type=self.MONITOR_TYPE)

    def get_third_party_info(
        self, server_config: BaseServerConfig
    ) -> Optional[ThirdPartyInfo]:
        return None

    def get_components(self, integration_config: BaseServerConfig):
        raise NotImplementedError

    def on_integration_disabled(self, integration_config: BaseServerConfig):
        pass

    def on_integration_enabled(self, integration_config: BaseServerConfig) -> None:
        self.reporting_service.clean_error_message(integration_config.uid)
        self._report_third_party_data(integration_config)

    def _report_third_party_data(self, integration_config: BaseServerConfig) -> None:
        # This is the version of the monitor, since currently the shared logic exists
        # in airflow_monitor package we import this package and get the version
        metadata = {"monitor_version": airflow_monitor.__version__}

        # pylint: disable=assignment-from-none
        third_party_info = self.get_third_party_info(integration_config)
        if third_party_info and third_party_info.error_list:
            formatted_error_list = ", ".join(third_party_info.error_list)
            self.reporting_service.report_error(
                integration_config.uid,
                f"verify_environment_{integration_config.uid}",
                formatted_error_list,
            )

        if third_party_info and third_party_info.metadata:
            metadata.update(third_party_info.metadata)

        self.reporting_service.report_metadata(integration_config.uid, metadata)
